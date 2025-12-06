import scrapy
from gov_data.items import GovDataItem
from datetime import datetime
import re

class GdGovSpider(scrapy.Spider):
    name = 'gd_gov'
    allowed_domains = ['gd.gov.cn']
    base_url = 'https://www.gd.gov.cn/zwgk/gsgg/index'
    
    # Increase page limit to ensure full coverage
    # Set to 50 for now, can be increased if needed
    # Default to incremental (1 page) unless specified
    
    def __init__(self, *args, **kwargs):
        super(GdGovSpider, self).__init__(*args, **kwargs)
        self.mode = kwargs.get('mode', 'incremental')
        if self.mode == 'incremental':
            self.max_pages = 1
            self.logger.info("Running in INCREMENTAL mode: Only checking homepage.")
        else:
            self.max_pages = int(kwargs.get('max_pages', 50))
            self.logger.info(f"Running in FULL mode: Checking up to {self.max_pages} pages.")

    def start_requests(self):
        # Start with page 1
        yield scrapy.Request(
            url=f"{self.base_url}.html",
            callback=self.parse_list,
            meta={'page': 1}
        )

    def parse_list(self, response):
        page = response.meta.get('page', 1)
        self.logger.info(f"Parsing list page {page}: {response.url}")
        
        # Try multiple selectors for list items
        # 1. Standard list
        li_tags = response.css('div.con li, ul.list li, div.list li')
        
        found_items = False
        file_extensions = ('.xls', '.xlsx', '.doc', '.docx', '.pdf', '.zip', '.rar', '.ofd')

        for li in li_tags:
            # Extract Title
            title = li.css('span.til a::text, a::text').get()
            # Extract URL
            url = li.css('span.til a::attr(href), a::attr(href)').get()
            # Extract Time
            publish_time_raw = li.css('span.time::text').get()
            publish_time = None
            if publish_time_raw:
                m = re.search(r'\d{4}[-/.]\d{2}[-/.]\d{2}', publish_time_raw)
                if m:
                    publish_time = m.group(0).replace('/', '-').replace('.', '-')
            
            if title and url:
                found_items = True
                title = title.strip()
                publish_time = publish_time.strip() if publish_time else datetime.now().strftime('%Y-%m-%d')
                
                full_url = response.urljoin(url)
                lower_url = full_url.lower()

                # Check if it is a direct file link
                if lower_url.endswith(file_extensions):
                    self.logger.info(f"Found direct file link: {full_url}")
                    item = GovDataItem()
                    item['title'] = title
                    item['publishDate'] = publish_time
                    item['sourceUrl'] = full_url
                    item['sourceOrg'] = '广东省人民政府'
                    item['region'] = '广东'
                    item['contentText'] = "详见附件"
                    
                    # Determine extension
                    ext = 'dat'
                    for e in file_extensions:
                        if lower_url.endswith(e):
                            ext = e.replace('.', '')
                            break
                            
                    item['attachments'] = [{
                        "name": title,
                        "url": full_url,
                        "type": ext
                    }]
                    yield item
                else:
                    # Normal detail page
                    meta_data = {
                        'title': title,
                        'publishDate': publish_time,
                        'sourceUrl': full_url,
                        'sourceOrg': '广东省人民政府',
                        'region': '广东'
                    }
                    
                    yield scrapy.Request(
                        url=full_url,
                        callback=self.parse_detail,
                        meta={'item_data': meta_data}
                    )
        
        if not found_items:
            self.logger.warning(f"No items found on page {page}, stopping pagination.")
            return

        # Pagination: Yield next page if we haven't reached the limit
        if page < self.max_pages:
            next_page = page + 1
            next_url = f"{self.base_url}_{next_page}.html"
            yield scrapy.Request(
                url=next_url,
                callback=self.parse_list,
                meta={'page': next_page}
            )

    def parse_detail(self, response):
        item_data = response.meta['item_data']
        
        # 1. Identify Main Content Area
        # Priority: class='zw', class='view_con', class='content', class='article'
        content_selectors = ['div.zw', 'div.view_con', 'div.content', 'div.article', 'div.news_cont']
        content_div = None
        
        for selector in content_selectors:
            div = response.css(selector)
            if div:
                content_div = div
                break
        
        # If still not found, fall back to body (risky, but better than nothing)
        if not content_div:
            content_div = response.css('body')

        # 2. Extract Text Content
        # Get all text paragraphs
        if content_div:
            paragraphs = content_div.css('p::text, div::text').getall()
            content_text = "\n\n".join([p.strip() for p in paragraphs if p.strip()])
        else:
            content_text = "正文内容提取失败"

        # 3. Extract Attachments
        attachments = []
        file_extensions = ('.xls', '.xlsx', '.doc', '.docx', '.pdf', '.zip', '.rar', '.ofd')
        
        # Look for links within the content area
        # Exclude common navigational links if searching broadly
        links = content_div.css('a')
        
        for link in links:
            href = link.css('::attr(href)').get()
            name = link.css('::text').get() or "Unnamed File"
            
            if href:
                lower_href = href.lower()
                if lower_href.endswith(file_extensions) or 'download' in lower_href:
                    full_url = response.urljoin(href)
                    
                    # Simple type detection
                    ext = 'dat'
                    for e in file_extensions:
                        if lower_href.endswith(e):
                            ext = e.replace('.', '')
                            break
                    
                    # Avoid duplicates
                    if not any(att['url'] == full_url for att in attachments):
                        attachments.append({
                            "name": name.strip(),
                            "url": full_url,
                            "type": ext
                        })

        # 4. Create Item
        item = GovDataItem()
        item['title'] = item_data['title']
        item['sourceOrg'] = item_data['sourceOrg']
        item['sourceUrl'] = item_data['sourceUrl']
        item['publishDate'] = item_data['publishDate']
        item['region'] = item_data['region']
        item['contentText'] = content_text
        item['attachments'] = attachments
        
        yield item
