# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class ThreeDgameItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


class PhoneGameItem(scrapy.Item):
    search_key = scrapy.Field()  # 搜索关键字
    game_type = scrapy.Field()   # 类型
    game_name = scrapy.Field()     # 名称
    publish_time = scrapy.Field()    # 上线时间
    game_category = scrapy.Field()  # 所属类别
    developer = scrapy.Field()  # 开发者
    platform = scrapy.Field()   # 使用平台
    pic = scrapy.Field()    # 游戏图片
