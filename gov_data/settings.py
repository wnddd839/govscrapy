# Scrapy settings for gov_data project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = "gov_data"

SPIDER_MODULES = ["gov_data.spiders"]
NEWSPIDER_MODULE = "gov_data.spiders"

ADDONS = {}


# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = "gov_data (+http://www.yourdomain.com)"

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Concurrency and throttling settings
#CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 1
DOWNLOAD_DELAY = 1

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#    "Accept-Language": "en",
#}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    "gov_data.middlewares.GovDataSpiderMiddleware": 543,
#}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    "gov_data.middlewares.GovDataDownloaderMiddleware": 543,
    "gov_data.middlewares.RandomUserAgentMiddleware": 500,  # 随机User-Agent
    "gov_data.middlewares.ProxyMiddleware": 600,  # IP代理池
    "gov_data.middlewares.RetryMiddleware": 700,  # 请求重试
    "scrapy.downloadermiddlewares.retry.RetryMiddleware": None,  # 禁用默认重试中间件
}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
#}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
   "gov_data.pipelines.RedisPipeline": 300,
}

# Redis Configuration
# Load from config/redis_config.yml
import os
import yaml

# Load Redis config
REDIS_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'redis_config.yml')
with open(REDIS_CONFIG_PATH, 'r', encoding='utf-8') as f:
    redis_config = yaml.safe_load(f)['redis']

REDIS_HOST = redis_config['host']
REDIS_PORT = redis_config['port']
REDIS_PASSWORD = redis_config['password']
REDIS_DB = redis_config['db']  # Set to 1 as required
REDIS_SOCKET_TIMEOUT = redis_config['socket_timeout']
REDIS_RETRY_TIMES = redis_config['retry_times']
REDIS_RETRY_INTERVAL = redis_config['retry_interval']

# Crawl Rules Config Path
CRAWL_RULES_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'crawl_rules.yml')

# Category Config Path
CATEGORY_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'category_config.yml')

# MinIO Configuration
MINIO_ENDPOINT = '8.138.24.168:19002'
MINIO_ACCESS_KEY = 'minioadmin'
MINIO_SECRET_KEY = 'minioadmin'
MINIO_BUCKET = 'gov-attachments'
MINIO_SECURE = False  # Set to True if using HTTPS

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = "httpcache"
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
FEED_EXPORT_ENCODING = "utf-8"
