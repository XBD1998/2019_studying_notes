import scrapy
from scrapy.selector import Selector
import json
import os
from ..items import juejinItem
from pymongo import MongoClient
from scrapy.conf import settings


class JuejinSpider(scrapy.Spider):
    name = "juejin"

    def __init__(self):
        self.item = juejinItem()
        self.isLest = True
        self.client = MongoClient(settings['MONGO_HOST'],settings['MONGO_PORT'])
        self.db = self.client[settings['MONGO_DB']]

    def start_requests(self):
        
        fo = open(os.path.abspath(os.path.dirname(os.path.dirname(__file__)))+"/juejin.tpl", "r+", encoding="utf-8")
        istr = fo.read()
        fo.close()
        for quote, timg, name in zip(Selector(text=istr).css('.item .tag').re(r'st:state[=\'\"\s]+([^\'\"]*)[\'\"]?[\s\S]*'), Selector(text=istr).css('.item .lazy').re(r'data-src[=\'\"\s]+([^\'\"]*)[\'\"]?[\s\S]*'), Selector(text=istr).css('.item .title::text')):
            self.timg = timg
            self.db['tags'].insert_one({
					'name': name.extract(),
					'id': quote,
					'timg': timg
				})
            
            ipage = 0
            while ipage < scrapy.conf.settings['JUEJIN_PAGE']:   
                ipage += 1
                if self.isLest:
                    tag_url = "https://timeline-merger-ms.juejin.im/v1/get_tag_entry?src=web&tagId="+ quote +"&page="+ str(ipage) +"&pageSize=1&sort=rankIndex"
                    yield scrapy.Request(url=tag_url, callback=self.parse_c)
                else:
                    self.isLest = True
                    break



    def parse_c(self, response):
        
        sites = json.loads(response.body_as_unicode())
        if sites['s'] == 1:
            for article in  sites['d']['entrylist']:
                self.item['objectId'] = article['objectId']
                self.item['dec'] = article['content']
                self.item['time'] = article['createdAt']
                self.item['utime'] = article['updatedAt']
                self.item['title'] = article['title']

                tags = []
                for tag in article['tags']:
                    tags.append({
                        'name': tag['title'],
                        'id': tag['id']
                        })
                self.item['tag'] = tags

                yield scrapy.Request(url=article['originalUrl'], callback=self.parse_s)
        else:
            self.isLest = False

    def parse_s(self, response):
        content = response.css('.post-content-container').extract_first()
        if content:
            self.item['content'] = content
        yield self.item





