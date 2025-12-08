import scrapy
from gov_data.items import GovDataItem
from datetime import datetime
import re

class HnGovSpider(scrapy.Spider):
    name = 'hn_gov'
    allowed_domains = ['hainan.gov.cn']

    custom_settings = {
        'DOWNLOAD_DELAY': 2,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 2,
        'RETRY_TIMES': 3,
        'DEFAULT_REQUEST_HEADERS': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
    }

    # Configuration for different sections
    SECTIONS = {
        "gwyzk": {
            "base_url": "https://www.hainan.gov.cn/hainan/gwyzk",
            "list_index": 3,
            "name": "招考招聘",
            "list_classes": ["list_div", "mar-top2"],
            "title_classes": ["list-right_title", "fon_1"],
            "time_attrs": {"width": "50%", "align": "left"}
        },
        "gbrm": {
            "base_url": "https://www.hainan.gov.cn/hainan/gbrm",
            "list_index": 3,
            "name": "人事任免",
            "list_classes": ["list_div", "mar-top2"],
            "title_classes": ["list-right_title", "fon_1"],
            "time_attrs": {"width": "50%", "align": "left"}
        },
        "rqgs": {
            "base_url": "https://www.hainan.gov.cn/hainan/rqgs",
            "list_index": 3,
            "name": "人事任免",
            "list_classes": ["list_div", "mar-top2"],
            "title_classes": ["list-right_title", "fon_1"],
            "time_attrs": {"width": "50%", "align": "left"}
        }
    }

    def __init__(self, *args, **kwargs):
        super(HnGovSpider, self).__init__(*args, **kwargs)
        # category can be a specific key from SECTIONS or 'all'
        self.category = kwargs.get('category', 'all')
        self.mode = kwargs.get('mode', 'incremental')
        self.max_pages = int(kwargs.get('max_pages', 50))
        
        if self.mode == 'incremental':
            self.max_pages = 2  # Check first 2 pages for incremental
            self.logger.info("Running in INCREMENTAL mode.")
        else:
            self.logger.info(f"Running in FULL mode: Checking up to {self.max_pages} pages.")

    def start_requests(self):
        categories_to_crawl = []
        if self.category == 'all':
            categories_to_crawl = list(self.SECTIONS.keys())
        elif self.category in self.SECTIONS:
            categories_to_crawl = [self.category]
        else:
            self.logger.error(f"Invalid category: {self.category}")
            return

        for cat_key in categories_to_crawl:
            config = self.SECTIONS[cat_key]
            base_url = config['base_url']
            list_index = config['list_index']
            
            # Start from page 1
            url = f"{base_url}/list{list_index}.shtml"
            yield scrapy.Request(
                url, 
                callback=self.parse_list, 
                meta={
                    'page': 1, 
                    'cat_key': cat_key,
                    'config': config
                },
                dont_filter=True
            )

    def _extract_date(self, text):
        if not text:
            return None
        # Clean up common prefixes
        text = text.replace("发布时间：", "").replace("发表时间：", "").strip()
        m = re.search(r'\d{4}[-/.]\d{2}[-/.]\d{2}', text)
        if m:
            d = m.group(0).replace('/', '-').replace('.', '-')
            return d
        return None

    def parse_list(self, response):
        page = response.meta.get('page', 1)
        cat_key = response.meta.get('cat_key')
        config = response.meta.get('config')
        
        self.logger.info(f"Parsing {config['name']} list page {page}: {response.url}")

        # Check for empty/error page
        tip_text = response.xpath('string(//body)').get() or ''
        if '抱歉，您访问的网页不存在或已删除' in tip_text:
            self.logger.warning("Warm-tip page encountered, stopping this category.")
            return

        found_items = False
        
        # 1. Try to find list items using configured classes
        list_items = []
        for cls in config.get('list_classes', []):
            if cls == 'zfwj_list': # Special handling for table
                items = response.css('table.zfwj_list tr')
                if items:
                    list_items.extend(items)
            else:
                items = response.css(f'div.{cls}')
                if items:
                    list_items.extend(items)
        
        # Fallback if no specific classes found
        if not list_items:
             list_items = response.css('div.list_div, div.mar-top2')

        for item_node in list_items:
            # Extract title and link
            title_node = None
            title = ""
            url = ""
            
            # Try configured title classes
            for title_cls in config.get('title_classes', []):
                t_node = item_node.css(f'div.{title_cls} a')
                if t_node:
                    title_node = t_node
                    break
            
            if not title_node:
                # Fallback: direct 'a' tag
                title_node = item_node.css('a')
            
            if title_node:
                title = (title_node.css('::text').get() or title_node.css('::attr(title)').get() or '').strip()
                url = title_node.css('::attr(href)').get()

            # Extract date
            # Try configured time attributes (usually for td)
            time_attrs = config.get('time_attrs', {})
            publish_time = None
            
            if time_attrs:
                # Construct css selector for td with attributes
                # e.g. td[width="50%"][align="left"]
                attr_selector = "".join([f'[{k}="{v}"]' for k, v in time_attrs.items()])
                time_node = item_node.css(f'td{attr_selector}')
                if time_node:
                    raw_time = time_node.css('::text').get()
                    publish_time = self._extract_date(raw_time)
            
            if not publish_time:
                # Fallback: search in text
                text_all = item_node.xpath('string(.)').get() or ''
                publish_time = self._extract_date(text_all)

            if title and url:
                found_items = True
                full_url = response.urljoin(url)
                publish_time = (publish_time or datetime.now().strftime('%Y-%m-%d')).strip()
                
                # Check if it's a file directly
                file_extensions = ('.xls', '.xlsx', '.doc', '.docx', '.pdf', '.zip', '.rar', '.ofd')
                lower_url = full_url.lower()
                
                if lower_url.endswith(file_extensions):
                    # It's a file
                    item = GovDataItem()
                    item['title'] = title
                    item['publishDate'] = publish_time
                    item['sourceUrl'] = full_url
                    item['sourceOrg'] = '海南省人民政府'
                    item['region'] = '海南'
                    item['category'] = config['name']  # Set category from config
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
                    # It's a detail page
                    meta_data = {
                        'title': title,
                        'publishDate': publish_time,
                        'sourceUrl': full_url,
                        'sourceOrg': '海南省人民政府',
                        'region': '海南',
                        'category': config['name']  # Pass category to detail
                    }
                    yield scrapy.Request(
                        full_url, 
                        callback=self.parse_detail, 
                        meta={'item_data': meta_data}
                    )

        if not found_items:
            self.logger.warning(f"No items found on {config['name']} page {page}.")
        
        # Pagination
        if page < self.max_pages:
            next_page = page + 1
            base_url = config['base_url']
            list_index = config['list_index']
            next_url = f"{base_url}/list{list_index}_{next_page}.shtml"
            
            yield scrapy.Request(
                next_url, 
                callback=self.parse_list, 
                meta={
                    'page': next_page, 
                    'cat_key': cat_key,
                    'config': config
                }
            )

    def parse_detail(self, response):
        item_data = response.meta['item_data']
        
        # Content extraction
        content_selectors = [
            'div#font', 
            'div.content', 
            'div.main-content', 
            'div#content', 
            'div.article-content',
            'div.TRS_Editor', 
            'div.view', 
            'div.xl_cont'
        ]
        
        content_div = None
        for selector in content_selectors:
            div = response.css(selector)
            if div:
                content_div = div
                break
        
        if not content_div:
            # Fallback to body but try to exclude nav/footer if possible (simple body for now)
            content_div = response.css('body')

        # Remove scripts, styles, etc.
        # Scrapy selectors don't have decompose(), need to use just text extraction or cleaner
        # We will just extract all text nodes
        paragraphs = content_div.css('p::text, div::text, span::text').getall()
        content_text = "\n".join([p.strip() for p in paragraphs if p.strip()])
        
        # Attachment extraction
        attachments = []
        file_extensions = ('.xls', '.xlsx', '.doc', '.docx', '.pdf', '.zip', '.rar', '.ofd')
        
        # 1. From links in content
        links = content_div.css('a')
        for link in links:
            href = link.css('::attr(href)').get()
            name = (link.css('::text').get() or '').strip()
            
            if href:
                lower_href = href.lower()
                if any(ext in lower_href for ext in file_extensions):
                    full_url = response.urljoin(href)
                    
                    # Determine extension
                    ext = 'dat'
                    for e in file_extensions:
                        if e in lower_href:
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
        
        item = GovDataItem()
        item['title'] = item_data['title']
        item['sourceOrg'] = item_data['sourceOrg']
        item['sourceUrl'] = item_data['sourceUrl']
        item['publishDate'] = item_data['publishDate']
        item['region'] = item_data['region']
        item['category'] = item_data.get('category', '其他')
        item['contentText'] = content_text
        item['attachments'] = attachments
        
        yield item
