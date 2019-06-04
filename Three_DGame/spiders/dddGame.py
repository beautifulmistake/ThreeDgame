import json
import os

import redis
import scrapy
from scrapy.exceptions import CloseSpider
from scrapy.signals import spider_closed
from scrapy.spidermiddlewares.httperror import HttpError
from scrapy_redis.spiders import RedisSpider
from twisted.internet.error import TimeoutError, TCPTimedOutError, DNSLookupError

from Three_DGame.items import PhoneGameItem


class DddGameSpider(scrapy.Spider):
    name = "dddGame"

    def __init__(self, settings):
        super().__init__()
        self.record_file = open(os.path.join(settings.get("JSON_PATH"), f'{self.name}.json'), "w+", encoding="utf8")
        self.record_file.write('[')
        self.keyword_file_list = os.listdir(settings.get("KEYWORD_PATH"))
        # 请求的接口---> type：1--->单机游戏  2---->手游    3---->网游    4---->页游
        self.base_url = 'https://so.3dmgame.com/?keyword={0}&type={1}'

    def start_requests(self):
        # 判断关键字文件是否存在
        if not self.keyword_file_list:
            # 抛出异常并关闭爬虫
            raise CloseSpider("需要关键字文件")
        # 遍历关键字文件路径
        for keyword_file in self.keyword_file_list:
            # 获取关键字文件路径
            file_path = os.path.join(self.settings.get("KEYWORD_PATH"), keyword_file)
            # 读取关键字文件
            with open(file_path, 'r', encoding='utf-8') as f:
                # 测试代码
                # for keyword in f.readlines()[33:34]:
                for keyword in f.readlines():
                    # 消除末尾的空格
                    keyword = keyword.strip()
                    for index in range(1, 5):
                        # 发起请求
                        yield scrapy.Request(url=self.base_url.format(keyword, index),
                                             meta={'search_key': keyword, 'type': str(index)})

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        # 获取配置信息
        settings = crawler.settings
        # 爬虫
        spider = super(DddGameSpider, cls).from_crawler(crawler, settings, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=spider_closed)
        return spider

    def spider_closed(self, spider):
        # 输出日志：关闭爬虫
        self.logger.info('Spider closed: %s', spider.name)
        spider.record_file.write("]")
        spider.record_file.close()

    def parse(self, response):
        """
        请求分为：
        1、单机----->type:1
        2、手游----->type:2
        3、网游----->type:3
        4、页游----->type:4
        根据type值的不同获取详情页的链接后调用不同的解析方式
        :param response:
        :return:
        """
        # 获取搜索关键字
        search_key = response.meta['search_key']
        # 获取type
        type_ = response.meta['type']
        # 查看获取的响应内容
        print("查看获取的响应内容：", response.text)
        # 不管是那种type的请求都采取统一的解析详情页的方式
        # 获取目前搜索的类型
        game_type = response.xpath('//div[@class="search_title"]/p/text()').extract_first()
        # 获取搜索结果数
        counts = response.xpath('//div[@class="search_title"]/div[@class="sech_top"]/p/span/text()').extract_first()
        # 判断counts
        if counts != "0":
            # 判断type的值
            if type_ == "1":
                # 采集详情页的链接
                detail_urls = response.xpath('//div[@class="search_wrap"]/'
                                             'div[@class="search_lis lis_djzq"]/a[1]/@href').extract()
                # 请求详情页
                for detail_url in detail_urls:
                    yield scrapy.Request(url=detail_url, callback=self.parse_detail,
                                         meta={'search_key': search_key, 'type': game_type})
                # 获取下一页链接
                next_page = response.xpath('//div[@id="kkpager"]/div/span/a[@title=">"]/@href').extract_first()
                if next_page:
                    yield scrapy.Request(url=next_page, callback=self.parse,
                                         meta={'search_key': search_key, 'type': type_})
            elif type_ == "2":
                detail_urls = response.xpath('//div[@class="search_wrap"]/'
                                             'div[@class="search_lis lis_syxz"]/a[1]/@href').extract()
                # 请求详情页
                for detail_url in detail_urls:
                    yield scrapy.Request(url=detail_url, callback=self.parse_detail,
                                         meta={'search_key': search_key, 'type': game_type})
                # 获取下一页链接
                next_page = response.xpath('//div[@id="kkpager"]/div/span/a[@title=">"]/@href').extract_first()
                if next_page:
                    yield scrapy.Request(url=next_page, callback=self.parse,
                                         meta={'search_key': search_key, 'type': type_})
            elif type_ == "3":
                detail_urls = response.xpath('//div[@class="search_wrap"]/'
                                             'div[@class="search_lis lis_olzq"]/a[1]/@href').extract()
                # 请求详情页
                for detail_url in detail_urls:
                    yield scrapy.Request(url=detail_url, callback=self.parse_detail,
                                         meta={'search_key': search_key, 'type': game_type})
                # 获取下一页链接
                next_page = response.xpath('//div[@id="kkpager"]/div/span/a[@title=">"]/@href').extract_first()
                if next_page:
                    yield scrapy.Request(url=next_page, callback=self.parse,
                                         meta={'search_key': search_key, 'type': type_})
            elif type_ == "4":
                detail_urls = response.xpath('//div[@class="search_wrap"]/'
                                             'div[@class="search_lis lis_yyzq"]/a[1]/@href').extract()
                # 请求详情页
                for detail_url in detail_urls:
                    yield scrapy.Request(url=detail_url, callback=self.parse_detail,
                                         meta={'search_key': search_key, 'type': game_type})
                # 获取下一页链接
                next_page = response.xpath('//div[@id="kkpager"]/div/span/a[@title=">"]/@href').extract_first()
                if next_page:
                    yield scrapy.Request(url=next_page, callback=self.parse,
                                         meta={'search_key': search_key, 'type': type_})

        # 将索索结果写入文件
        self.record_file.write(json.dumps({"search_key": search_key, "counts": counts, "type": game_type},
                                          ensure_ascii=False))
        self.record_file.write(",\n")
        self.record_file.flush()

    def parse_detail(self, response):
        """
        跟据type的类型采取不同的解析方式
       :param response:
        :return:
        """
        # 创建item对象
        item = PhoneGameItem()
        # 搜索关键字
        search_key = response.meta['search_key']
        print("查看当前搜索关键字：", search_key)
        # 游戏类型
        game_type = response.meta['type']
        print("查看当前游戏类型：", game_type)
        # print("查看响应：****************", response.text)
        # 判断type的类型：单机专区---->手游下载---->网游专区---->页游专区
        if game_type == "单机专区":
            # 单机专区---游戏名称
            game_name = response.xpath('//div[@class="Gminfo"]/div[@class="info"]/div/child::*/text()').extract_first()
            # 上线时间
            publish_time = response.xpath('//div[@class="Gminfo"]/div[@class="info"]/ul/li[1]/text()').extract_first()
            # 游戏类型
            game_category = response.xpath('//div[@class="Gminfo"]/div[@class="info"]/ul/li[2]/text()').extract_first()
            # 游戏发行者
            developer = response.xpath('//div[@class="Gminfo"]/div[@class="info"]/ul/li[4]/text()').extract_first()
            # 平台
            platform = response.xpath('//div[@class="Gminfo"]/div[@class="info"]/ul/li[5]/text()').extract_first()
            # 图片
            pic = response.xpath('//div[@class="Gminfo"]/div[@class="img"]/img/@src').extract_first()
            item['search_key'] = search_key
            item['game_type'] = game_type
            item['game_name'] = game_name
            item['publish_time'] = publish_time
            item['game_category'] = game_category
            item['developer'] = developer
            item['platform'] = platform
            item['pic'] = pic
            yield item
        elif game_type == "手游下载":
            # 游戏名称
            game_name = response.xpath('//div[@class="content"]/div[@class="detail-top"]'
                                       '/div[@class="bt"]/child::*/text()').extract_first()
            # 上线时间
            publish_time = response.xpath('//div[@class="content"]/div[@class="detail-top"]'
                                          '/div[@class="Gminfo"]/ul/li[4]/text()').extract_first()
            # 游戏类型
            game_category = response.xpath('//div[@class="content"]/div[@class="detail-top"]'
                                           '/div[@class="Gminfo"]/ul/li[3]/text()').extract_first()
            # 发行者
            developer = response.xpath('//div[@class="content"]/div[@class="detail-top"]'
                                       '/div[@class="Gminfo"]/ul/li[5]/text()').extract_first()
            # 平台
            platform = response.xpath('//div[@class="content"]/div[@class="detail-top"]'
                                      '/div[@class="Gminfo"]/ul/li[2]/child::*/text()').extract_first()
            # 图片
            pic = response.xpath('//div[@class="content"]/div[@class="detail-top"]'
                                 '/div[@class="Gminfo"]/div[@class="img"]/img/@src').extract_first()
            item['search_key'] = search_key
            item['game_type'] = game_type
            item['game_name'] = game_name
            item['publish_time'] = publish_time
            item['game_category'] = game_category
            item['developer'] = developer
            item['platform'] = platform
            item['pic'] = pic
            yield item
        elif game_type == "网游专区":
            # 单机专区---游戏名称
            game_name = response.xpath('//div[@class="content"]/div[@class="ar_bottom"]'
                                       '/div[@class="rit_bot"]/div/ul/li[1]/text()').extract_first()
            # 上线时间
            publish_time = "暂无"
            # 游戏类型
            game_category = response.xpath('//div[@class="content"]/div[@class="ar_bottom"]'
                                           '/div[@class="rit_bot"]/div/ul/li[9]/child::*/child::*/text()').extract_first()
            # 游戏发行者
            developer = response.xpath('//div[@class="content"]/div[@class="ar_bottom"]'
                                       '/div[@class="rit_bot"]/div/ul/li[5]/child::*/text()').extract_first()
            # 平台
            platform = response.xpath('//div[@class="content"]/div[@class="ar_bottom"]'
                                      '/div[@class="rit_bot"]/div/ul/li[3]/child::*/child::*/text()').extract_first()
            # 图片
            pic = response.xpath('//div[@class="content"]/div[@class="ar_bottom"]'
                                 '/div[@class="rit_bot"]/div[@class="item1"]/img/@src').extract_first()
            item['search_key'] = search_key
            item['game_type'] = game_type
            item['game_name'] = game_name
            item['publish_time'] = publish_time
            item['game_category'] = game_category
            item['developer'] = developer
            item['platform'] = platform
            item['pic'] = pic
            yield item
        elif game_type == "页游专区":
            # 单机专区---游戏名称
            game_name = response.xpath('//div[@class="content"]/div/div/div[@class="Tlaft"]/p/text()').extract_first()
            # 上线时间
            publish_time = "暂无"
            # 游戏类型
            game_category = response.xpath('//div[@class="content"]/div/div/div[@class="miaoshu"]'
                                           '/div[@class="bq"]/child::*/text()').extract_first()
            # 游戏发行者
            developer = "暂无"
            # 平台
            platform = "暂无"
            # 图片
            pic = response.xpath('//div[@class="content"]/div/div/div[@class="Tlaft"]/a/img/@src').extract_first()
            item['search_key'] = search_key
            item['game_type'] = game_type
            item['game_name'] = game_name
            item['publish_time'] = publish_time
            item['game_category'] = game_category
            item['developer'] = developer
            item['platform'] = platform
            item['pic'] = pic
            yield item
