# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

import random
from scrapy import signals
from fake_useragent import UserAgent

# useful for handling different item types with a single interface
from itemadapter import ItemAdapter


class GovDataSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    async def process_start(self, start):
        # Called with an async iterator over the spider start() method or the
        # maching method of an earlier spider middleware.
        async for item_or_request in start:
            yield item_or_request

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class GovDataDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class RandomUserAgentMiddleware:
    """
    随机User-Agent中间件
    使用fake-useragent生成随机User-Agent
    """
    def __init__(self):
        self.ua = UserAgent()
    
    def process_request(self, request, spider):
        # 设置随机User-Agent
        request.headers['User-Agent'] = self.ua.random
        spider.logger.debug(f"🔀 Set User-Agent: {request.headers['User-Agent']}")
        return None


class ProxyMiddleware:
    """
    IP代理池中间件
    可配置代理列表，随机选择使用
    """
    def __init__(self):
        # 代理列表（可从外部配置加载）
        self.proxies = [
            # "http://proxy1:port",
            # "http://proxy2:port",
            # "http://proxy3:port",
        ]
    
    def process_request(self, request, spider):
        if self.proxies:
            proxy = random.choice(self.proxies)
            request.meta['proxy'] = proxy
            spider.logger.debug(f"🔀 Set Proxy: {proxy}")
        return None


class RetryMiddleware:
    """
    请求重试中间件
    对失败请求进行重试
    """
    def __init__(self):
        self.retry_times = 3  # 重试次数
        self.retry_http_codes = [408, 429, 500, 502, 503, 504]  # 需要重试的HTTP状态码
    
    def process_response(self, request, response, spider):
        if response.status in self.retry_http_codes:
            spider.logger.warning(f"⚠️ Response status {response.status} for {request.url}, retrying...")
            return request.copy()
        return response
    
    def process_exception(self, request, exception, spider):
        # 对请求异常进行重试
        retry_count = request.meta.get('retry_count', 0)
        if retry_count < self.retry_times:
            retry_count += 1
            request.meta['retry_count'] = retry_count
            spider.logger.warning(f"⚠️ Exception for {request.url}, retrying {retry_count}/{self.retry_times}...")
            return request.copy()
        spider.logger.error(f"❌ Failed after {self.retry_times} retries for {request.url}")
        return None
