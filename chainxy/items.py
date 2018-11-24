# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field

class ChainItem(Item):
    title = Field()
    desc = Field() 
    image = Field()
    stars = Field()
    quality = Field()
    imdb_code = Field()
    keywords = Field()
    genres = Field()
    year = Field()
    eps = Field()
    type = Field()
    server_f1 = Field()
    server_f2 = Field()
    vidnode = Field()
    rapidvideo = Field()
    streamango = Field()
    openload1 = Field()
    openload2 = Field()
    first_air_date = Field()
    