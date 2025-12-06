import scrapy
from gov_data.items import GovDataItem
from datetime import datetime

class GovListSpider(scrapy.Spider):
    name = 'gov_list'
    allowed_domains = ['hainan.gov.cn']
    base_url = 'https://www.hainan.gov.cn/hainan/gwyzk/list3{}.shtml'

    # Configuration
    total_pages = 10
    retry_times = 1

    def start_requests(self):
        for page in range(1, self.total_pages + 1):
            url_suffix = '' if page == 1 else f'_{page}'
            full_url = self.base_url.format(url_suffix)
            yield scrapy.Request(
                url=full_url,
                callback=self.parse_list,
                meta={'page': page, 'retry_count': 0},
                dont_filter=True
            )

    def parse_list(self, response):
        page = response.meta['page']
        self.logger.info(f"📄 Parsing list page {page}: {response.url}")

        div_list = response.css('div.list_div, div.mar-top2')
        if not div_list:
            self.logger.warning(f"⚠️ No list data found on page {page}")
            return

        for div in div_list:
            title = div.css('div.list-right_title a::text, div.fon_1 a::text').get()
            sub_url = div.css('div.list-right_title a::attr(href), div.fon_1 a::attr(href)').get()
            publish_time = div.css('td[width="50%"][align="left"]::text').get()

            if title and sub_url and publish_time:
                title = title.strip()
                sub_url = response.urljoin(sub_url)
                publish_time = publish_time.replace('发布时间：', '').strip()

                # Normalize Date to YYYY-MM-DD
                # Assuming format is YYYY-MM-DD or similar
                # If it fails, we pass it as is, and pipeline handles fallback
                
                meta_data = {
                    'title': title,
                    'publishDate': publish_time,
                    'sourceUrl': sub_url,
                    'sourceOrg': '海南省人力资源和社会保障厅', # Default/Hardcoded as per example implies
                    'region': '海南'
                }

                yield scrapy.Request(
                    url=sub_url,
                    callback=self.parse_detail,
                    meta={'item_data': meta_data}
                )

    def parse_detail(self, response):
        item_data = response.meta['item_data']
        
        # 1. Extract Content
        # Try common selectors for content
        content_selectors = [
            'div.view_con', 
            'div.content', 
            'div.xl_con', 
            'div#zoom', 
            'div.TRS_Editor'
        ]
        content_text = ""
        for selector in content_selectors:
            content = response.css(selector).get()
            if content:
                # We want text, but maybe keeping HTML is better? 
                # Requirement says "contentText": "公告正文内容..."
                # Usually this implies text or cleaned HTML. 
                # Let's store the raw text of the content div for now to be safe, or inner HTML.
                # Example shows "公告正文内容...", implying text.
                # Let's get all text within the div.
                content_text = response.css(f'{selector} *::text').getall()
                content_text = "\n".join([t.strip() for t in content_text if t.strip()])
                break
        
        if not content_text:
             # Fallback to body text if no container found (risky but better than empty)
             content_text = response.css('body *::text').getall()
             content_text = "\n".join([t.strip() for t in content_text if t.strip()])

        # 2. Extract Attachments
        attachments = []
        # Find all links that look like files
        file_extensions = ('.xls', '.xlsx', '.doc', '.docx', '.pdf', '.zip', '.rar')
        links = response.css('a')
        for link in links:
            href = link.css('::attr(href)').get()
            name = link.css('::text').get()
            
            if href and href.lower().endswith(file_extensions):
                full_url = response.urljoin(href)
                ext = href.split('.')[-1]
                attachments.append({
                    "name": name.strip() if name else "Unknown File",
                    "url": full_url,
                    "type": ext
                })

        # 3. Create Item
        item = GovDataItem()
        item['title'] = item_data['title']
        item['sourceOrg'] = item_data['sourceOrg']
        item['sourceUrl'] = item_data['sourceUrl']
        item['publishDate'] = item_data['publishDate']
        item['region'] = item_data['region']
        item['contentText'] = content_text
        item['attachments'] = attachments
        
        yield item
