# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

class GovDataItem(scrapy.Item):
    title = scrapy.Field()
    sourceOrg = scrapy.Field()
    sourceUrl = scrapy.Field()
    publishDate = scrapy.Field()
    region = scrapy.Field()
    contentText = scrapy.Field()
    attachments = scrapy.Field()
