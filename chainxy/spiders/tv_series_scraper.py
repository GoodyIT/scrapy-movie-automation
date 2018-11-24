import scrapy
import json
import re
import csv
import requests
from scrapy.spiders import Spider
from scrapy.http import FormRequest
from scrapy.http import Request
from scrapy.selector import HtmlXPathSelector
from chainxy.items import ChainItem

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC

from bs4 import BeautifulSoup as BSoup
from lxml import etree
import time

import pdb

class FMovies_scraper(scrapy.Spider):
    name = "tv_series_scraper"

    domain = "https://www9.fmovies.io"
    start_urls = ["https://www9.fmovies.io/latest/tv-series.html"]
    wp_url = "http://911movies.co/wp-login.php"
    add_movie_url = 'http://911movies.co/wp-admin/post-new.php?post_type=tvshows'
    update_movie_url = 'http://911movies.co/wp-admin/post.php?post='
    seasons_url = 'http://911movies.co/wp-admin/edit.php?post_type=tvshows'
    episodes_url = 'http://911movies.co/wp-admin/edit.php?post_type=episodes'
    store_id = []
    data = []
    movies_cnt = 0
    counter = 0

    def __init__(self):
        prof = webdriver.FirefoxProfile()
        prof.set_preference('dom.webnotifications.enabled', False)

        opts = webdriver.FirefoxOptions()
        # opts.set_headless(headless=True)

        self.driver = webdriver.Firefox( 
            firefox_profile=prof,
            firefox_options=opts,
            executable_path='./data/geckodriver.exe')

    def start_requests(self):
        yield scrapy.Request(url=self.start_urls[0], callback=self.parse_hot_series)

    # calculate number of pages
    def parse_hot_series(self, response):
        try:
            movies = response.xpath("//figure")
            self.movies_cnt = len(movies)
            for movie in movies:
                tooltip = movie.xpath(".//div[@class='tooltip']")
                title = tooltip.xpath(".//div[@class='title']/text()").extract_first()
                genres = ";".join(tooltip.xpath(".//div[@class='meta']")[1].xpath(".//a/text()").extract())
                stars = ";".join(tooltip.xpath(".//div[@class='meta']")[2].xpath(".//a/text()").extract())
                eps = 0
                try:
                    eps = movie.xpath(".//div[@class='eps']/div/text()").extract_first()
                except:
                    eps = 0
                item = ChainItem(title=title, genres=genres, stars=stars, eps=eps, type="series")
                sub_url = movie.xpath(".//a")[0].xpath(".//@href").extract_first()
                request = scrapy.Request(url=self.domain+sub_url, callback=self.parse_movie_detail)
                request.meta['item'] = item
                yield request
                return;
        
            # get the pagination if there is more movies
            # pagination = response.xpath(".//ul[@class='pagination'][1]//li[@class='selected']/following::li/a/@href").extract()
            # if len(pagination) > 0:
            #     for query in pagination:
            #         yield scrapy.Request(url=self.start_urls[0]+query, callback=self.parse_hot_series)
           
        except:
            pdb.set_trace()

    def parse_movie_detail(self, response):
        detail = response.xpath("//div[@class='detail']")
        quality = detail.xpath(".//span[@class='quanlity']/text()").extract_first()
        keywords = ";".join(detail.xpath(".//div[@class='keywords']/a/text()").extract())
        try:
            year = detail.xpath(".//div[@class='meta'][2]/div[2]/text()").extract_first().split(':')[1].strip()
        except:
            year = ''
        item = response.meta['item']
        item['desc'] = self.validate(detail.xpath(".//div[@class='detail-r']/div[@class='desc']/text()").extract_first())
        item['quality'] = quality
        item['keywords'] = keywords
        item['year'] = year

        url = "https://api.themoviedb.org/3/search/tv?api_key=dffc13fdbbda3c30005665c5dfa3fdab&language=en-US&page=1&query=" + item['title'].split('-')[0]
        headers = {
            'Accept': 'text/html, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Cookie': 'uu=BCYj_lCs3v-FXbzw_W8B2F1XL7L2_d7nlugV1ty9zvbgsCDKAl9yM94hbFq2iokb5VSL5LvbUQi_%0D%0AOP5SEa5JOWGmu3kblYLQRf_k7PoEcAqhA3E7HFIZIn_vj3KBYpd4eZFn8CwzGLlCo2fN1Y5_xlyV%0D%0ARELuUtAjqth8353dhX_yLKwZY5oIk47ppTJiNDYh3EzqeeYNf3k6ZY2rCilTGgCFFbkxeP0m5Jwe%0D%0AiO3SiqSaaXrPaUfn72iDXR89yq7ngI2YOiKIZsaIwfBWZnoMPfmBXw%0D%0A; session-id=138-1917369-9346350; session-id-time=2166558376; ubid-main=131-3852723-3124332; session-token=Y4A5pmQ7Ob1ICD0hECYVhI13mVPEWf+a2clO8Q4QRQB1f19Kkhouv8Qzube7bu6JyqxdyQuYgNsl6Okv+88QkB11iVXYlJOUYOz+1eQNwX1z9vhrwNjGYbgLwJOr/AHozpHUPDjoeK80DwaSbJYvaKy/niTNR8KqZ9RNyMZUuB9p6ZdKskEfmxcF/PFTgW/J; as=%7B%22h%22%3A%7B%22t%22%3A%5B0%2C0%5D%2C%22tr%22%3A%5B0%2C0%5D%2C%22ib%22%3A%5B0%2C0%5D%7D%2C%22n%22%3A%7B%22t%22%3A%5B0%2C0%5D%2C%22tr%22%3A%5B0%2C0%5D%2C%22in%22%3A%5B0%2C0%5D%2C%22ib%22%3A%5B0%2C0%5D%7D%7D; csm-hit=tb:DGX34ZK2VFWQ1D80WQ62+s-DGX34ZK2VFWQ1D80WQ62|1535885947713&adb:adblk_no',
            'Host': 'www.imdb.com',
            'Referer': 'https://www.imdb.com/plugins',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest'
        }

        request = scrapy.Request(url, callback=self.parse_imdb_code)
        request.meta['item'] = item

        yield request
    
    def parse_imdb_code(self, response):
        item = response.meta['item']
        json_data = json.loads(response.body)
        if len(json_data['results']) > 0:
            item['imdb_code'] = json_data['results'][0]['id']
            item['first_air_date'] = json_data['results'][0]['first_air_date']

        self.data.append(item)
        self.counter += 1
        print('------------ counter -----------', self.counter , ' ----- movies --- ', self.movies_cnt)
        # if self.movies_cnt == self.counter:
        self.counter = 0
        yield Request("https://stackoverflow.com/", callback=self.parse_dummy)

    def parse_dummy(self, response):
        print("New session is started ------------ ******* ----------")
        # pdb.set_trace()
        self.driver.get(self.wp_url)
        time.sleep(1)
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, "wp-submit")))
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, "user_login"))).send_keys("Thanh")
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, "user_pass"))).send_keys("vb&c5Q7aNqXORT(8Tehm2Yqz")
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, "wp-submit"))).click()

        time.sleep(1)
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, "menu-posts-movies")))
        url = 'http://911movies.co/wp-json/custom/v1/all-posts?search=' + self.data[self.counter]['title'].split('-')[0]
        yield scrapy.Request(url, self.search_movie)

    def search_movie(self, response):
        search_result = json.loads(response.body)
        if search_result and  len(search_result) > 0:
            # update the existing movie
            url = self.update_movie_url + str(search_result[0]['id'] ) + '&action=edit'
            self.driver.get(url)
        else:
            # add new movie
            self.driver.get(self.add_movie_url)
        
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, "ids"))).clear()
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, "ids"))).send_keys(self.data[self.counter]['imdb_code'])
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//tr[@id='ids_box']//input[@type='button']"))).click()
        time.sleep(2)
        print(" -- Add New Movie Page ------------ ******* ----------")

        # Add SEO title
        seo_title = 'Watch ' + self.data[self.counter]['title'] + ' ' + self.data[self.counter]['year'] + ' Online Free, 911movies'
        # WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//div[@id='aiosp_title_wrapper']//input[@name='aiosp_title']"))).send_keys(seo_title)

        # Add SEO Keywords
        # seo_keywords = "action;"
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//div[@id='aiosp_keywords_wrapper']//input[@name='aiosp_keywords']"))).clear()
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//div[@id='aiosp_keywords_wrapper']//input[@name='aiosp_keywords']"))).send_keys(seo_title)

        # Add description
        # pdb.set_trace()
        # time.sleep(1)
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//div[@id='aiosp_description_wrapper']//textarea[@name='aiosp_description']"))).clear()
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//div[@id='aiosp_description_wrapper']//textarea[@name='aiosp_description']"))).send_keys(self.data[self.counter]['desc'])

        # pdb.set_trace()
        # Add Genres
        pdb.set_trace()
        for genre in self.data[self.counter]['genres'].split(';'):
            try:
                WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//ul[@id='genreschecklist']//label[contains(., '"+ genre +"')]/input"))).click()
            except:
                pass

        # Add Quality
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//div[@id='dtquality']//input[@id='new-tag-dtquality']"))).clear()
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//div[@id='dtquality']//input[@id='new-tag-dtquality']"))).send_keys(self.data[self.counter]['quality'])
        # WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//div[@id='dtquality']//input[@type='button']"))).click()
        self.driver.find_elements_by_xpath(".//div[@id='dtquality']//input[@type='button']")[0].click()

        # Add Creator
        # WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//div[@id='dtdirector']//input[@type='button']"))).send_keys("")
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//div[@id='dtcreator']//input[@type='button']"))).click()

        # Add Casts
        # WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//div[@id='dtcast']//input[@type='button']"))).send_keys("")
        self.driver.find_elements_by_xpath(".//div[@id='dtcast']//input[@type='button']")[0].click()
        # WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//div[@id='dtcast']//input[@type='button']"))).click()

        # Add Studio
        self.driver.find_elements_by_xpath(".//div[@id='dtstudio']//input[@type='button']")[0].click()

        # Add Networks
        self.driver.find_elements_by_xpath(".//div[@id='dtnetworks']//input[@type='button']")[0].click()

        # Add Year
        # WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//div[@id='dtyear']//input[@type='button']"))).send_keys("")
        # WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//div[@id='dtyear']//input[@type='button']"))).click()
        self.driver.find_elements_by_xpath(".//div[@id='dtyear']//input[@type='button']")[0].click()
        self.driver.find_elements_by_id("publish")[0].click()

        yield Request(self.seasons_url, callback=self.search_seasons)

    def search_seasons(self, response):
        pdb.set_trace()
        
    
    def validate(self, value):
        if value:
            return value.strip()
        else:
            return ""




        

