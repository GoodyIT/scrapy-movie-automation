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

class Auto_Post(scrapy.Spider):
    name = "auto_post"

    domain = "http://911movies.co/wp-admin/"
    wp_url = "http://911movies.co/wp-login.php"
    add_movie_url = 'http://911movies.co/wp-admin/post-new.php?post_type=movies'
    update_movie_url = 'http://911movies.co/wp-admin/post.php?post='

    data = {
        'id': '1',
        'title': 'Blood Fest',
        'imdbcode': 'tt7208564',
        'quality': 'HD 720',
        'genres': ';Comedy;Horror',
        'year': '2018',
        'server_f1': '//vidcloud.icu/streaming.php?id=MjE1OTc4&title=Blood Fest',
        'server_f2': '',
        'vidnode': '//vidcloud.icu/load.php?id=MjE1OTc4&title=Blood Fest',
        'rapidvideo': 'https://www.rapidvideo.com/e/FUTOMF1FL',
        'streamango': 'https://streamango.com/embed/dpofksrkbamqname',
        'openload1': 'https://openload.co/embed/Bm0FhS8Cl_E',
        'openload2': '',
    }

    store_id = []

    def __init__(self):
        self.option = webdriver.ChromeOptions()
        # self.option.add_argument('headless')
        self.option.add_argument('blink-settings=imagesEnabled=false')
        self.option.add_argument('--ignore-certificate-errors')
        self.option.add_argument('--ignore-ssl-errors')
        self.option.add_argument("--no-sandbox")
        self.option.add_argument("--disable-impl-side-painting")
        self.option.add_argument("--disable-setuid-sandbox")
        self.option.add_argument("--disable-seccomp-filter-sandbox")
        self.option.add_argument("--disable-breakpad")
        self.option.add_argument("--disable-client-side-phishing-detection")
        self.option.add_argument("--disable-cast")
        self.option.add_argument("--disable-cast-streaming-hw-encoding")
        self.option.add_argument("--disable-cloud-import")
        self.option.add_argument("--disable-popup-blocking")
        self.option.add_argument("--disable-session-crashed-bubble")
        self.option.add_argument("--disable-ipv6")
        self.driver = webdriver.Chrome(executable_path='./data/chromedriver.exe', chrome_options=self.option)

    def start_requests(self):
        yield Request("https://stackoverflow.com/", callback=self.parse_dummy)

    def parse_dummy(self, response):
        print("New session is started ------------ ******* ----------")
        self.driver.get(self.wp_url)
        time.sleep(1)
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, "wp-submit")))
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, "user_login"))).send_keys("Thanh")
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, "user_pass"))).send_keys("vb&c5Q7aNqXORT(8Tehm2Yqz")
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, "wp-submit"))).click()

        time.sleep(1)
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, "menu-posts-movies")))
        url = 'http://911movies.co/wp-json/custom/v1/all-posts?search=' + self.data['title']
        yield scrapy.Request(url, self.search_movie)

    def search_movie(self, response):
        pdb.set_trace();
        search_result = json.loads(response.body)
        if  len(search_result) > 0:
            # update the existing movie
            url = self.update_movie_url + str(search_result[0]['id'] ) + '&action=edit'
            self.driver.get(url)
        else:
            # add new movie
            self.driver.get(self.add_movie_url)
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, "ids"))).send_keys(self.data['imdbcode'])
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//tr[@id='ids_box']//input[@type='button']"))).click()
            time.sleep(2)
            print(" -- Add New Movie Page ------------ ******* ----------")

            # Add SEO title
            seo_title = 'Watch ' + self.data['title'] + ' ' + self.data['year'] + ' Online Free, 911movies'
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//div[@id='aiosp_title_wrapper']//input[@name='aiosp_title']"))).send_keys(seo_title)

            # Add SEO Keywords
            # seo_keywords = "action;"
            # WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//div[@id='aiosp_keywords_wrapper']//input[@name='aiosp_keywords']"))).send_keys(seo_keywords)

            # pdb.set_trace()
            # Add Genres
            for genre in self.data['genres'].split(';'):
                try:
                    WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//ul[@id='genreschecklist']//label[contains(., '"+ genre +"')]/input"))).click()
                except:
                    pass

            # Add Quality
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//div[@id='dtquality']//input[@id='new-tag-dtquality']"))).send_keys(self.data['quality'])
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//div[@id='dtquality']//input[@type='button']"))).click()

            # Add Director
            # WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//div[@id='dtdirector']//input[@type='button']"))).send_keys("")
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//div[@id='dtdirector']//input[@type='button']"))).click()

            # Add Casts
            # WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//div[@id='dtcast']//input[@type='button']"))).send_keys("")
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//div[@id='dtcast']//input[@type='button']"))).click()

            # Add Year
            pdb.set_trace()
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//div[@id='dtyear']//input[@type='button']"))).send_keys("")
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//div[@id='dtyear']//input[@type='button']"))).click()

        # Add Video Links
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//tr[@class='tritem']//input[@name='name[]']"))).send_keys('server_f1')
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//tr[@class='tritem']//input[@name='url[]']"))).send_keys(self.data['server_f1'])
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//select[@name='idioma[]']/option[text()='English']"))).click()

        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "add_row"))).click()
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//tr[@class='tritem'][2]//input[@name='name[]']"))).send_keys('server_f2')
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//tr[@class='tritem'][2]//input[@name='url[]']"))).send_keys(self.data['server_f2'])
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//tr[@class='tritem'][2]//select[@name='idioma[]']/option[text()='English']"))).click()

        pdb.set_trace()
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "add_row"))).click()
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//tr[@class='tritem'][3]//input[@name='name[]']"))).send_keys('vidnode')
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//tr[@class='tritem'][3]//input[@name='url[]']"))).send_keys(self.data['vidnode'])
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//tr[@class='tritem'][3]//select[@name='idioma[]']/option[text()='English']"))).click()
        
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "add_row"))).click()
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//tr[@class='tritem'][4]//input[@name='name[]']"))).send_keys('rapidvideo')
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//tr[@class='tritem'][4]//input[@name='url[]']"))).send_keys(self.data['rapidvideo'])
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//tr[@class='tritem'][4]//select[@name='idioma[]']/option[text()='English']"))).click()

        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "add_row"))).click()
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//tr[@class='tritem'][5]//input[@name='name[]']"))).send_keys('streamango')
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//tr[@class='tritem'][5]//input[@name='url[]']"))).send_keys(self.data['streamango'])
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//tr[@class='tritem'][5]//select[@name='idioma[]']/option[text()='English']"))).click()

        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "add_row"))).click()
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//tr[@class='tritem'][6]//input[@name='name[]']"))).send_keys('openload1')
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//tr[@class='tritem'][6]//input[@name='url[]']"))).send_keys(self.data['openload1'])
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//tr[@class='tritem'][6]//select[@name='idioma[]']/option[text()='English']"))).click()

        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "add_row"))).click()
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//tr[@class='tritem'][6]//input[@name='name[]']"))).send_keys('openload2')
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//tr[@class='tritem'][6]//input[@name='url[]']"))).send_keys(self.data['openload2'])
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//tr[@class='tritem'][6]//select[@name='idioma[]']/option[text()='English']"))).click()

        # Publish
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, "publish"))).send_keys("")
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, "publish"))).click()

        # yield Request("https://stackoverflow.com/", callback=self.parse_dummy)

    def validate(self, value):
        if value != None:
            return value.strip().replace(u'\u2019', '-').replace('&#8217;', "'")
        else:
            return ""




        

