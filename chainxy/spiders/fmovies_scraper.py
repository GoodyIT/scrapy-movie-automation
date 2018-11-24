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
    name = "fmovies_scraper"

    domain = "https://www9.fmovies.io"
    start_urls = ["https://www9.fmovies.io/latest/movies.html"]
    wp_url = "http://911movies.co/wp-login.php"
    add_movie_url = 'http://911movies.co/wp-admin/post-new.php?post_type=movies'
    update_movie_url = 'http://911movies.co/wp-admin/post.php?post='
    data = []
    movies_cnt = 0
    counter = 0
    temp = 0

    def __init__(self):
        # self.option = webdriver.ChromeOptions()
        # # self.option.add_argument('headless')
        # self.option.add_argument('blink-settings=imagesEnabled=false')
        # self.option.add_argument('--ignore-certificate-errors')
        # self.option.add_argument('--ignore-ssl-errors')
        # self.option.add_argument("--no-sandbox")
        # self.option.add_argument("--disable-impl-side-painting")
        # self.option.add_argument("--disable-setuid-sandbox")
        # self.option.add_argument("--disable-seccomp-filter-sandbox")
        # self.option.add_argument("--disable-breakpad")
        # self.option.add_argument("--disable-client-side-phishing-detection")
        # self.option.add_argument("--disable-cast")
        # self.option.add_argument("--disable-cast-streaming-hw-encoding")
        # self.option.add_argument("--disable-cloud-import")
        # self.option.add_argument("--disable-popup-blocking")
        # self.option.add_argument("--disable-session-crashed-bubble")
        # self.option.add_argument("--disable-ipv6")
        # self.driver = webdriver.Chrome(executable_path='./data/chromedriver.exe', chrome_options=self.option)
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
                image = movie.xpath(".//a/img/@src").extract_first()
                genres = ";" + ";".join(tooltip.xpath(".//div[@class='meta']")[1].xpath(".//a/text()").extract())
                stars = ";".join(tooltip.xpath(".//div[@class='meta']")[2].xpath(".//a/text()").extract())
                eps = 0
                try:
                    eps = movie.xpath(".//div[@class='eps']/div/text()").extract_first()
                except:
                    eps = 0
                item = ChainItem(title=title, image=image, genres=genres, stars=stars, eps=eps, type="movie")
                sub_url = movie.xpath(".//a")[0].xpath(".//@href").extract_first()
                request = scrapy.Request(url=self.domain+sub_url, callback=self.parse_movie_detail)
                request.meta['item'] = item
                yield request
                # if self.movies_cnt > 1:
                # return
        
            # get the pagination if there is more movies
            # pagination = response.xpath(".//ul[@class='pagination'][1]//li[@class='selected']/following::li/a/@href").extract()
            # if len(pagination) > 0:
            #     for query in pagination:
            #         yield scrapy.Request(url=self.start_urls[0]+query, callback=self.parse_hot_series)
            #         return
           
        except:
            pdb.set_trace()

    def parse_movie_detail(self, response):
        item = response.meta['item']
        try:
            detail = response.xpath("//div[@class='detail']")
            quality = detail.xpath(".//span[@class='quanlity']/text()").extract_first()
            keywords = ",".join(detail.xpath(".//div[@class='keywords']/a/text()").extract())
   
            item['quality'] = quality
            
            item['desc'] = self.validate(detail.xpath(".//div[@class='detail-r']/div[@class='desc']/text()").extract_first())
            item['keywords'] = keywords
            try:
                year = detail.xpath(".//div[@class='meta'][2]/div[2]/text()").extract_first().split(':')[1].strip()
                item['year'] = year
            except:
                item['year'] = ''
            
            try:
                item['server_f1'] = self.validate(response.xpath(".//article[@id='server-f2']/div[@class='big-player']/@data-video").extract_first().split('&typesub')[0])
            except:
                pdb.set_trace()
                item['server_f1'] = ''
                
            try:
                item['server_f2'] = self.validate(response.text.split('var link_server_f2 = ')[1].split('var link_server_vidnode = ')[0].split(';')[0][1:-1])
            except:
                item['server_f2'] = ''
            
            try:
                item['vidnode'] = self.validate(response.text.split('var link_server_vidnode = ')[1].split('var link_server_ocloud = ')[0].split(';')[0][1:-1])
            except:
                item['vidnode'] = ''
                
            try:
                item['rapidvideo'] = self.validate(response.text.split('var link_server_ocloud = ')[1].split('var link_server_streamango = ')[0].split('";')[0][1:]) 
            except:
                item['rapidvideo'] = ''
                
            try:
                item['streamango'] = self.validate(response.text.split('var link_server_streamango = ')[1].split('var link_server_openload = ')[0].split(';')[0][1:-1])
            except:
                item['streamango'] = ''
           
            try:
                openload = response.text.split('var link_server_openload = ')[1]
                item['openload1'] = openload.split('var link_server_openload = ')[0].split(';')[0][1:-1]
                item['openload2'] = openload.split('var link_server_openload = ')[1].split('$(document).ready(function')[0][1:-1]
            except:
                item['openload1'] = ''
                item['openload2'] = ''
        except:
            print('--------------- error -------------- ');
        
        url = "https://www.imdb.com/plugins/_ajax?q=" + item['title']
        request = scrapy.Request(url, self.parse_imdb_code)
        request.meta['item'] = item

        self.temp += 1
        print('------- url ----------', response.url, '------- count--------', self.temp)

        yield request
    
    def parse_imdb_code(self, response):
        item = response.meta['item']
        item['imdb_code'] = response.xpath(".//li/@data-tconst").extract_first()
        self.data.append(item)
        self.counter += 1
        print('------------ counter -----------', self.counter , ' ----- movies --- ', self.movies_cnt)
        # pdb.set_trace()
        if self.movies_cnt == self.counter + 1:
            self.counter = 0
            print(self.data)
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

        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, "menu-posts-movies")))
        url = 'http://911movies.co/wp-json/custom/v1/all-posts?search=' + self.data[self.counter]['title']
        yield scrapy.Request(url, self.search_movie)

    def search_movie(self, response):
        # pdb.set_trace();
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
        print('--------------desc-------------', self.data)
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//div[@id='aiosp_description_wrapper']//textarea[@name='aiosp_description']"))).clear()
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//div[@id='aiosp_description_wrapper']//textarea[@name='aiosp_description']"))).send_keys(self.data[self.counter]['desc'])

        # pdb.set_trace()
        # Add Genres
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

        # Add Director
        # WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//div[@id='dtdirector']//input[@type='button']"))).send_keys("")
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//div[@id='dtdirector']//input[@type='button']"))).click()

        # Add Casts
        # WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//div[@id='dtcast']//input[@type='button']"))).send_keys("")
        self.driver.find_elements_by_xpath(".//div[@id='dtcast']//input[@type='button']")[0].click()
        # WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//div[@id='dtcast']//input[@type='button']"))).click()

        # Add Year
        # WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//div[@id='dtyear']//input[@type='button']"))).send_keys("")
        # WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//div[@id='dtyear']//input[@type='button']"))).click()
        self.driver.find_elements_by_xpath(".//div[@id='dtyear']//input[@type='button']")[0].click()

        # Add Video Links
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//tr[@class='tritem']//input[@name='name[]']"))).clear()
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//tr[@class='tritem']//input[@name='url[]']"))).clear()
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//tr[@class='tritem']//input[@name='name[]']"))).send_keys('server_f1')
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//tr[@class='tritem']//input[@name='url[]']"))).send_keys(self.data[self.counter]['server_f1'])
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//select[@name='idioma[]']/option[text()='English']"))).click()

        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "add_row"))).click()
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//tr[@class='tritem'][2]//input[@name='name[]']"))).clear()
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//tr[@class='tritem'][2]//input[@name='url[]']"))).clear()
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//tr[@class='tritem'][2]//input[@name='name[]']"))).send_keys('server_f2')
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//tr[@class='tritem'][2]//input[@name='url[]']"))).send_keys(self.data[self.counter]['server_f2'])
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//tr[@class='tritem'][2]//select[@name='idioma[]']/option[text()='English']"))).click()

        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "add_row"))).click()
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//tr[@class='tritem'][3]//input[@name='name[]']"))).clear()
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//tr[@class='tritem'][3]//input[@name='url[]']"))).clear()
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//tr[@class='tritem'][3]//input[@name='name[]']"))).send_keys('vidnode')
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//tr[@class='tritem'][3]//input[@name='url[]']"))).send_keys(self.data[self.counter]['vidnode'])
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//tr[@class='tritem'][3]//select[@name='idioma[]']/option[text()='English']"))).click()
        
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "add_row"))).click()
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//tr[@class='tritem'][4]//input[@name='name[]']"))).clear()
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//tr[@class='tritem'][4]//input[@name='url[]']"))).clear()
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//tr[@class='tritem'][4]//input[@name='name[]']"))).send_keys('rapidvideo')
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//tr[@class='tritem'][4]//input[@name='url[]']"))).send_keys(self.data[self.counter]['rapidvideo'])
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//tr[@class='tritem'][4]//select[@name='idioma[]']/option[text()='English']"))).click()

        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "add_row"))).click()
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//tr[@class='tritem'][5]//input[@name='name[]']"))).clear()
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//tr[@class='tritem'][5]//input[@name='url[]']"))).clear()
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//tr[@class='tritem'][5]//input[@name='name[]']"))).send_keys('streamango')
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//tr[@class='tritem'][5]//input[@name='url[]']"))).send_keys(self.data[self.counter]['streamango'])
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//tr[@class='tritem'][5]//select[@name='idioma[]']/option[text()='English']"))).click()

        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "add_row"))).click()
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//tr[@class='tritem'][6]//input[@name='name[]']"))).clear()
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//tr[@class='tritem'][6]//input[@name='url[]']"))).clear()
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//tr[@class='tritem'][6]//input[@name='name[]']"))).send_keys('openload1')
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//tr[@class='tritem'][6]//input[@name='url[]']"))).send_keys(self.data[self.counter]['openload1'])
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//tr[@class='tritem'][6]//select[@name='idioma[]']/option[text()='English']"))).click()

        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "add_row"))).click()
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//tr[@class='tritem'][7]//input[@name='name[]']"))).clear()
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//tr[@class='tritem'][7]//input[@name='url[]']"))).clear()
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//tr[@class='tritem'][7]//input[@name='name[]']"))).send_keys('openload2')
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//tr[@class='tritem'][7]//input[@name='url[]']"))).send_keys(self.data[self.counter]['openload2'])
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//tr[@class='tritem'][7]//select[@name='idioma[]']/option[text()='English']"))).click()

        # Publish
        # WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, "publish"))).send_keys("")
       
        # WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, "publish"))).click()
        self.driver.find_elements_by_id("publish")[0].click()

        time.sleep(3)
        self.counter += 1
        if self.counter < self.movies_cnt-1:
            url = 'http://911movies.co/wp-json/custom/v1/all-posts?search=' + self.data[self.counter]['title']
            yield scrapy.Request(url, self.search_movie)
        else:
            self.driver.close()
    
    def validate(self, value):
        if value:
            return value.strip()
        else:
            return ""
    
    def catchValidate(self, value):
        value = ''
        try:
            value = value.strip()
        except:
            pdb.set_trace()
            value = ""
        return value


    



        

