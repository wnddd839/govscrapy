import scrapy
import yaml
import os
from scrapy import Request
from gov_data.items import GovDataItem


class ConfigBasedSpider(scrapy.Spider):
    """
    基于配置的动态爬虫
    从crawl_rules.yml加载爬取规则，支持多个网站的动态爬取
    """
    name = 'config_based_spider'
    allowed_domains = []
    
    def __init__(self, *args, **kwargs):
        super(ConfigBasedSpider, self).__init__(*args, **kwargs)
        # 加载爬取规则配置
        self.crawl_rules = self._load_crawl_rules()
        # 初始化allowed_domains
        self._init_allowed_domains()
    
    def _load_crawl_rules(self):
        """加载爬取规则配置"""
        rules_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config', 'crawl_rules.yml')
        try:
            with open(rules_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config.get('websites', [])
        except Exception as e:
            self.logger.error(f"Failed to load crawl rules: {e}")
            return []
    
    def _init_allowed_domains(self):
        """初始化allowed_domains"""
        for website in self.crawl_rules:
            if website.get('enabled', True):
                self.allowed_domains.extend(website.get('allowed_domains', []))
    
    def start_requests(self):
        """生成初始请求"""
        for website in self.crawl_rules:
            if not website.get('enabled', True):
                self.logger.info(f"Skipping disabled website: {website.get('website_name')}")
                continue
            
            self.logger.info(f"Starting crawl for website: {website.get('website_name')}")
            
            # 获取列表页配置
            list_config = website.get('list_page', {})
            start_page = list_config.get('start_page', 1)
            end_page = list_config.get('end_page', 10)
            url_template = list_config.get('url_template', '')
            
            if not url_template:
                self.logger.warning(f"No url_template for website: {website.get('website_name')}")
                continue
            
            # 生成列表页请求
            for page in range(start_page, end_page + 1):
                # 替换URL模板中的页码占位符
                url = url_template.format(page=page)
                self.logger.debug(f"Generated list page URL: {url}")
                
                yield Request(
                    url=url,
                    callback=self.parse_list,
                    meta={
                        'website': website,
                        'page': page
                    }
                )
    
    def parse_list(self, response):
        """解析列表页，生成详情页请求"""
        website = response.meta.get('website')
        page = response.meta.get('page')
        
        self.logger.info(f"Parsing list page {page} for {website.get('website_name')}: {response.url}")
        
        # 获取列表配置
        list_config = website.get('list_page', {})
        list_item_selector = list_config.get('list_item_selector')
        title_selector = list_config.get('title_selector')
        url_selector = list_config.get('url_selector')
        publish_time_selector = list_config.get('publish_time_selector')
        
        if not list_item_selector:
            self.logger.warning(f"No list_item_selector for website: {website.get('website_name')}")
            return
        
        # 提取列表项
        list_items = response.css(list_item_selector)
        self.logger.info(f"Found {len(list_items)} items on page {page}")
        
        for item in list_items:
            # 提取标题
            title = item.css(title_selector).get()
            if not title:
                continue
            
            # 提取URL
            url = item.css(url_selector).get()
            if not url:
                continue
            
            # 提取发布时间
            publish_time_raw = item.css(publish_time_selector).get()
            
            # 生成详情页请求
            detail_url = response.urljoin(url)
            self.logger.debug(f"Generated detail page URL: {detail_url}")
            
            yield Request(
                url=detail_url,
                callback=self.parse_detail,
                meta={
                    'website': website,
                    'title': title.strip(),
                    'publish_time_raw': publish_time_raw.strip() if publish_time_raw else None
                }
            )
    
    def parse_detail(self, response):
        """解析详情页，生成Item"""
        website = response.meta.get('website')
        title = response.meta.get('title')
        publish_time_raw = response.meta.get('publish_time_raw')
        
        self.logger.info(f"Parsing detail page: {response.url}")
        
        # 获取详情页配置
        detail_config = website.get('detail_page', {})
        content_selectors = detail_config.get('content_selectors', [])
        content_text_selector = detail_config.get('content_text_selector')
        publish_dept_selector = detail_config.get('publish_dept_selector')
        attachment_selector = detail_config.get('attachment_selector')
        attachment_url_selector = detail_config.get('attachment_url_selector')
        attachment_name_selector = detail_config.get('attachment_name_selector')
        
        # 提取正文内容
        content = ""
        for selector in content_selectors:
            content_div = response.css(selector)
            if content_div:
                if content_text_selector:
                    paragraphs = content_div.css(content_text_selector).getall()
                    content = "\n\n".join([p.strip() for p in paragraphs if p.strip()])
                else:
                    content = content_div.get()
                break
        
        # 提取发布单位
        publish_dept = ""
        if publish_dept_selector:
            publish_dept = response.css(publish_dept_selector).get() or ""
        
        # 提取附件
        attachments = []
        if attachment_selector and attachment_url_selector:
            attachment_elements = response.css(attachment_selector)
            for att in attachment_elements:
                att_url = att.css(attachment_url_selector).get()
                if att_url:
                    att_name = att.css(attachment_name_selector).get() or "Unnamed File"
                    attachments.append({
                        'name': att_name.strip(),
                        'url': response.urljoin(att_url)
                    })
        
        # 创建Item
        item = GovDataItem()
        item['title'] = title
        item['sourceUrl'] = response.url
        item['publishDate'] = publish_time_raw
        item['sourceOrg'] = publish_dept.strip()
        item['content'] = content
        item['attachments'] = attachments
        item['sourceWebsite'] = website.get('website_name')
        
        yield item