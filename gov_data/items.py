# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

class GovDataItem(scrapy.Item):
    """
    政务公开信息数据模型
    与后端PublicInfo实体类完全对齐
    使用驼峰命名法
    """
    # 核心字段（与后端PublicInfo一致）
    dataId = scrapy.Field()        # UUID，32位无横线
    title = scrapy.Field()         # 信息标题（String(255)）
    content = scrapy.Field()       # 信息正文（Text）
    publishTime = scrapy.Field()   # 发布时间（YYYY-MM-DD HH:mm:ss）
    sourceUrl = scrapy.Field()     # 来源URL（String(512)）
    sourceWebsite = scrapy.Field() # 来源网站名称（String(100)）
    publishDept = scrapy.Field()   # 发布单位（String(100)）
    category = scrapy.Field()      # 分类标签（String(50)）
    crawlTime = scrapy.Field()     # 爬取时间（YYYY-MM-DD HH:mm:ss）
    isNew = scrapy.Field()         # 固定为1（标记未同步）
    
    # 辅助字段
    attachments = scrapy.Field()   # 附件列表
    region = scrapy.Field()        # 地区信息
    
    # 兼容原有字段（用于过渡）
    sourceOrg = scrapy.Field()     # 原有发布单位字段
    publishDate = scrapy.Field()   # 原有发布时间字段
    contentText = scrapy.Field()   # 原有正文字段
    source_url = scrapy.Field()    # 原有来源URL字段
    source_website = scrapy.Field() # 原有来源网站字段
    publish_dept = scrapy.Field()  # 原有发布单位字段
    category_tag = scrapy.Field()  # 原有分类标签字段
    data_id = scrapy.Field()       # 原有数据ID字段
    publish_time = scrapy.Field()  # 原有发布时间字段
    crawl_time = scrapy.Field()    # 原有爬取时间字段
    is_new = scrapy.Field()        # 原有同步状态字段
