import scrapy
from gov_data.items import GovDataItem
from datetime import datetime
import re

class HnGovSpider(scrapy.Spider):
    name = 'hn_gov'
    allowed_domains = ['hainan.gov.cn']

    custom_settings = {
        'DOWNLOAD_DELAY': 2,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'RETRY_TIMES': 2,
        'DEFAULT_REQUEST_HEADERS': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0'
        }
    }

    def __init__(self, *args, **kwargs):
        super(HnGovSpider, self).__init__(*args, **kwargs)
        # category: 'zfwj' (政策文件) or 'gwyzk' (公务员招考)
        self.category = kwargs.get('category', 'zfwj')
        self.mode = kwargs.get('mode', 'incremental')
        self.max_pages = int(kwargs.get('max_pages', 50))
        if self.mode == 'incremental':
            self.max_pages = 1
            self.logger.info("Running in INCREMENTAL mode: Only checking homepage.")
        else:
            self.logger.info(f"Running in FULL mode: Checking up to {self.max_pages} pages.")

    def start_requests(self):
        base = self._get_base_url()
        url = f"{base}/list{self._get_list_index()}.shtml"
        yield scrapy.Request(url, callback=self.parse_list, meta={'page': 1, 'base': base})

    def _extract_date(self, text):
        if not text:
            return None
        m = re.search(r'\d{4}[-/.]\d{2}[-/.]\d{2}', text)
        if m:
            d = m.group(0).replace('/', '-').replace('.', '-')
            return d
        return None

    def parse_list(self, response):
        page = response.meta.get('page', 1)
        base = response.meta.get('base')
        self.logger.info(f"Parsing list page {page}: {response.url}")

        # warm-tip page detection
        tip_text = response.xpath('string(//body)').get() or ''
        if '抱歉，您访问的网页不存在或已删除' in tip_text:
            self.logger.warning("Warm-tip page encountered, skipping.")
            return

        file_extensions = ('.xls', '.xlsx', '.doc', '.docx', '.pdf', '.zip', '.rar', '.ofd')
        found_items = False

        # selectors by category
        list_selectors = []
        if self.category == 'zfwj':
            list_selectors = [
                'table.zfwj_list tr',
                'div.list_div',
                'div.mar-top2'
            ]
        else:  # gwyzk
            list_selectors = [
                'div.list_div',
                'div.mar-top2'
            ]

        items = []
        for sel in list_selectors:
            nodes = response.css(sel)
            if nodes:
                items = nodes
                break

        if not items:
            # fallback broad selectors
            items = response.css('ul.list li, div.list li, div.main_list li, tr')

        for li in items:
            link = li.css('a')
            title = (link.css('::text').get() or link.css('::attr(title)').get() or '').strip()
            url = link.css('::attr(href)').get()

            raw_time = li.css('td[width="50%"][align="left"]::text').get() or li.css('span::text').get()
            publish_time = self._extract_date(raw_time)
            if not publish_time:
                text_all = li.xpath('string(.)').get() or ''
                publish_time = self._extract_date(text_all)

            if title and url:
                found_items = True
                publish_time = (publish_time or datetime.now().strftime('%Y-%m-%d')).strip()
                full_url = response.urljoin(url)

                lower_url = full_url.lower()
                if lower_url.endswith(file_extensions):
                    item = GovDataItem()
                    item['title'] = title
                    item['publishDate'] = publish_time
                    item['sourceUrl'] = full_url
                    item['sourceOrg'] = '海南省人民政府'
                    item['region'] = '海南'
                    item['contentText'] = '详见附件'
                    ext = 'dat'
                    for e in file_extensions:
                        if lower_url.endswith(e):
                            ext = e.replace('.', '')
                            break
                    item['attachments'] = [{
                        'name': title,
                        'url': full_url,
                        'type': ext
                    }]
                    yield item
                else:
                    meta_data = {
                        'title': title,
                        'publishDate': publish_time,
                        'sourceUrl': full_url,
                        'sourceOrg': '海南省人民政府',
                        'region': '海南'
                    }
                    yield scrapy.Request(full_url, callback=self.parse_detail, meta={'item_data': meta_data})

        if not found_items:
            self.logger.warning(f"No items found on page {page}. Trying link-based fallback.")
            for a in response.css('a[href]'):
                href = a.css('::attr(href)').get() or ''
                text = (a.css('::text').get() or '').strip()
                if self.category in href and len(text) >= 10:
                    full_url = response.urljoin(href)
                    meta_data = {
                        'title': text,
                        'publishDate': datetime.now().strftime('%Y-%m-%d'),
                        'sourceUrl': full_url,
                        'sourceOrg': '海南省人民政府',
                        'region': '海南'
                    }
                    yield scrapy.Request(full_url, callback=self.parse_detail, meta={'item_data': meta_data})

        # pagination
        if page < self.max_pages:
            next_page = page + 1
            next_url = f"{base}/list{self._get_list_index()}_{next_page}.shtml"
            yield scrapy.Request(next_url, callback=self.parse_list, meta={'page': next_page, 'base': base})

    def parse_detail(self, response):
        item_data = response.meta['item_data']
        
        content_selectors = ['div#font', 'div.TRS_Editor', 'div.view', 'div.content', 'div.article_content', 'div.xl_cont']
        content_div = None
        
        for selector in content_selectors:
            div = response.css(selector)
            if div:
                content_div = div
                break
        
        if not content_div:
            content_div = response.css('body')

        paragraphs = content_div.css('p::text, div::text').getall()
        content_text = "\n\n".join([p.strip() for p in paragraphs if p.strip()])
        
        attachments = []
        file_extensions = ('.xls', '.xlsx', '.doc', '.docx', '.pdf', '.zip', '.rar', '.ofd')
        search_areas = [
            content_div,
            response.css('div.fujian'),
            response.css('div.downfiles'),
            response.css('#attach'),
            response.css('#fj'),
            response.css('ul.attach'),
            response.css('div.xiazai'),
            response.css('div.filedown')
        ]

        for area in search_areas:
            for link in area.css('a'):
                href = link.css('::attr(href)').get()
                name = (link.css('::text').get() or '').strip()
                if not href:
                    continue
                lower_href = href.lower()
                if lower_href.endswith(file_extensions) or 'download' in lower_href:
                    full_url = response.urljoin(href)
                    ext = 'dat'
                    for e in file_extensions:
                        if lower_href.endswith(e):
                            ext = e.replace('.', '')
                            break
                    if not name:
                        name = full_url.split('/')[-1]
                    if not any(att['url'] == full_url for att in attachments):
                        attachments.append({
                            'name': name,
                            'url': full_url,
                            'type': ext
                        })

        if not attachments:
            html = response.text
            for m in re.finditer(r'href\s*=\s*["\']([^"\']+\.(?:xls|xlsx|pdf|doc|docx|zip|rar|ofd))', html, re.IGNORECASE):
                href = m.group(1)
                full_url = response.urljoin(href)
                ext = href.split('.')[-1].lower()
                name = full_url.split('/')[-1]
                if not any(att['url'] == full_url for att in attachments):
                    attachments.append({
                        'name': name,
                        'url': full_url,
                        'type': ext
                    })

        item = GovDataItem()
        item['title'] = item_data['title']
        item['sourceOrg'] = item_data['sourceOrg']
        item['sourceUrl'] = item_data['sourceUrl']
        item['publishDate'] = item_data['publishDate']
        item['region'] = item_data['region']
        item['contentText'] = content_text
        item['attachments'] = attachments
        
        yield item

    def _get_base_url(self):
        if self.category == 'gwyzk':
            return 'https://www.hainan.gov.cn/hainan/gwyzk'
        return 'https://www.hainan.gov.cn/hainan/zfwj'

    def _get_list_index(self):
        # zfwj uses list4, gwyzk uses list3 per your scripts
        return 3 if self.category == 'gwyzk' else 4
