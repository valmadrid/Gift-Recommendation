from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from random import randint
from time import sleep
import pandas as pd
import json
import re
import numpy as np
import os
import urllib
import datetime


class Sephora():

    prefix_url = "https://www.sephora.com"

    def __init__(self):
        # create a webdriver instance OR open a Chrome browser
        chrome_path = "/Users/valmadrid/Downloads/chromedriver"
        self.browser = webdriver.Chrome(executable_path=chrome_path)

    def close_login_box(self):
        try:
            # close pop-up window
            self.browser.find_element_by_xpath(
                "//*[@id='modalDialog']/button").click()
        except:
            pass

    def close_country_box(self):
        try:
            # close pop-up window
            self.browser.find_element_by_xpath(
                "//*[@id='MediaModal']/button").click()
        except:
            pass

    def scroll_to_bottom(self, n=5):
        # scrolls the browser down n times
        sleep(1)
        self.close_country_box()
        self.close_login_box()
        self.close_country_box()
        sleep(1)
        elem = self.browser.find_element_by_tag_name("body")
        no_of_pagedowns = n
        while no_of_pagedowns:
            elem.send_keys(Keys.PAGE_DOWN)
            sleep(0.5)
            self.close_country_box()
            self.close_login_box()
            self.close_country_box()
            no_of_pagedowns -= 1

    def next_page(self):
        try:
            # go to next browser page
            if self.browser.find_element_by_class_name(
                    "css-4ktkov").get_attribute("aria-label") == "Next":
                self.browser.find_element_by_class_name("css-4ktkov").click()
                sleep(1)
                self.close_country_box()
                self.close_login_box()
                self.close_country_box()
                self.scroll_to_bottom(20)
                sleep(1)
                self.close_country_box()
                self.close_login_box()
                self.close_country_box()
                sleep(1)
        except:
            pass

    def view_300(self):
        try:
            # view 300 items
            if self.browser.find_element_by_class_name(
                    "css-1qizhe3").text.endswith("View all"):
                self.browser.find_element_by_class_name(
                    "css-1qizhe3").send_keys("View all")
                sleep(1)
                self.close_country_box()
                self.close_login_box()
                self.close_country_box()
                self.scroll_to_bottom(20)
                sleep(1)
                self.close_country_box()
                self.close_login_box()
                self.close_country_box()
                sleep(1)
        except:
            pass

    def open_url(self, url):
        # open url in browser
        self.url = url
        self.browser.get(self.url)

        self.close_country_box()
        self.close_login_box()
        self.close_country_box()
        sleep(2)

        self.scroll_to_bottom(10)
        sleep(2)
        self.scroll_to_bottom(20)
        sleep(2)

        self.close_country_box()
        self.close_login_box()
        self.close_country_box()
        sleep(2)
        
    def get_brands(self):
        # get all brand urls
        a_elems = self.browser.find_elements_by_xpath("//a")
        self.brand_list=[]
        for a in a_elems:
            brand_dict={}
            if a.text != "" and a.get_attribute("href").startswith(
                "https://www.sephora.com/brand/"):
                brand_dict["brand_name"] = a.text.strip()
                brand_dict["brand_link"]= a.get_attribute("href")
                self.brand_list.append(brand_dict)

    def get_productsJSON(self):  
        # load browser's page_source into bs4
        self.soup = BeautifulSoup(self.browser.page_source, 'html.parser')
        self.soup.prettify()

        try:
            # look for text/json
            self.product_json = self.soup.find(
                attrs={"type": re.compile("text/json")})
            # convert into json format
            self.product_json = json.loads(self.product_json.text)

        except:
            pass

        self.product_list = []

        tag_remover = re.compile(
            "<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});|\r|\n|&#x?[^;]{2,4}")
        
        # get all products from json

        for i in self.product_json:
            for key, val in i["props"].items():
                if key == "products" and type(val) == list:
                    for product in val:
                        product_dict = {}
                        product_dict["brand_name"] = tag_remover.sub(
                            "", product["brandName"])
                        product_dict["product_id"] = product["productId"]
                        product_dict["product_sku"] = product["currentSku"][
                            "skuId"]
                        product_dict["product_name"] = tag_remover.sub(
                            "", product["displayName"])
                        product_dict["product_price_low"] = float(
                            product["currentSku"]["listPrice"].split(
                                "-")[0].strip().replace("$", ""))
                        product_dict["product_price_high"] = float(
                            product["currentSku"]["listPrice"].split(
                                "-")[-1].strip().replace("$", ""))
                        product_dict["product_rating"] = float(product["rating"])
                        product_dict[
                            "product_image"] = self.prefix_url + product[
                                "currentSku"]["skuImages"]["image450"]
                        product_dict[
                            "product_link"] = self.prefix_url + product[
                                "targetUrl"]

                        self.product_list.append(product_dict)

    def get_productsHTML(self):
        # load browser's page_source into bs4
        self.soup = BeautifulSoup(self.browser.page_source, 'html.parser')
        self.soup.prettify()

        try:
            # look for all class a's containing product info
            self.tags = self.soup.find_all("a", href=re.compile("/product/"))

        except:
            pass

        self.product_list = []

        tag_remover = re.compile(
            "<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});|\r|\n|&#x?[^;]{2,4}")
        ref_pattern = re.compile("P[0-9]+")
        item_pattern = re.compile("s[0-9]+")

        for tag in self.tags:
            product_dict = {}

            product_dict["brand_name"] = tag_remover.sub(
                            "", tag.find(attrs={
                "data-at":
                re.compile("sku_item_brand")
            }).get_text(strip=True)) if tag.find(
                attrs={"data-at": re.compile("sku_item_brand")}) else np.nan

            product_dict["product_id"] = ref_pattern.findall(
                tag.attrs["href"])[-1] if tag.attrs["href"] else np.nan

            product_dict["product_sku"] = item_pattern.findall(
                tag.find(attrs={
                    "src": re.compile("/productimages/")
                }).get("src"))[-1].strip("s") if tag.find(
                    attrs={"src": re.compile("/productimages/")}) else np.nan

            product_dict["product_name"] = tag_remover.sub(
                            "", tag.find(
                attrs={
                    "data-at": re.compile("sku_item_name")
                }).get_text(strip=True)) if tag.find(
                    attrs={"data-at": re.compile("sku_item_name")}) else np.nan

            product_dict["product_price_low"] = float(
                tag.find(attrs={
                    "data-at": re.compile("sku_item_price_list")
                }).get_text(strip=True).split("-")[0].strip().replace(
                    "$", "")) if tag.find(
                        attrs={"data-at": re.compile("sku_item_price_list")
                               }) else np.nan

            product_dict["product_price_high"] = float(
                tag.find(attrs={
                    "data-at": re.compile("sku_item_price_list")
                }).get_text(strip=True).split("-")[-1].strip().replace(
                    "$", "")) if tag.find(
                        attrs={"data-at": re.compile("sku_item_price_list")
                               }) else np.nan

            product_dict["product_rating"] = float(
                tag.find(attrs={
                    "data-comp": re.compile("StarRating")
                }).attrs["aria-label"].strip(" stars")) if tag.find(
                    attrs={"data-comp": re.compile("StarRating")}).attrs[
                "aria-label"].strip(" stars") !="No" else np.nan

            product_dict["product_image"] = self.prefix_url + tag.find(
                attrs={
                    "src": re.compile("/productimages/")
                }).get("src") if tag.find(
                    attrs={"src": re.compile("/productimages/")}) else np.nan

            product_dict["product_link"] = self.prefix_url + tag.attrs[
                "href"] if tag.attrs["href"] else np.nan

            self.product_list.append(product_dict)
            
    def get_product_info(self, id_, folder_path):
        self.id_ = id_
        self.file_path = folder_path + self.id_ + ".json"
        
        # load browser's page_source into bs4
        self.soup = BeautifulSoup(self.browser.page_source, 'html.parser')
        self.soup.prettify()

        try:
            # look for text/json
            self.product_desc = self.soup.find(
                attrs={"type": re.compile("text/json")})
            # convert into json format
            self.product_desc = json.loads(self.product_desc.text)

        except:
            pass 

        for i in self.product_desc:
            for key, val in i["props"].items():
                if key == "currentProduct" and type(val) == dict:
                    self.data = val
                    with open(self.file_path, "w") as outfile:
                        json.dump(self.data, outfile, indent=2)
                    break
            if os.path.isfile(self.file_path):
                break
    
    def get_image(self, sku, folder_path):
        self.image_url = self.prefix_url + "/productimages/sku/s" + str(sku) + "-main-Lhero.jpg"
        self.file_path = folder_path + self.id_ + ".png"
    
        r = requests.get(self.image_url, allow_redirects=True)
        if r.status_code==200:
            open(self.file_path, 'wb').write(r.content)

    def get_reviews(self, id_, folder_path):
        
        start_date = int(datetime.datetime(2015, 6, 26, 0, 0, 0).timestamp())
        end_date = int(datetime.datetime(2020, 6, 25, 23, 59, 59).timestamp())

        prefix = "https://api.bazaarvoice.com/data/reviews.json?apiversion=5.4&passkey=rwbw526r2e7spptqd2qzbkp7"
        filter_id = "&Filter=ProductId%3A{}".format(id_)
        filter_time = "&Filter=SubmissionTime:gte:{}&Filter=SubmissionTime:lte:{}".format(
            start_date, end_date)
#         filter_ratings = "&Filter=Rating:gte:3&Filter=IsRecommended:eq:true"
#         filter_ratings = "&Filter=Rating:lte:2&Filter=IsRecommended:eq:true"
        includes = "&Include=Products%2CComments&Stats=Reviews"
        
        for offset in range(-1, 10000):
            if offset == -1:
                continue
#                 page = "&Sort=SubmissionTime:desc&Limit=1&Offset=0"
#                 self.url = prefix + filter_id + includes + page
#                 self.file_path = folder_path+id_+"_stats.json"
#                 self.browser.get(self.url)
#                 self.data = json.loads(self.browser.find_element_by_xpath("/html/body/pre").text)
#                 with open(self.file_path, "w") as outfile:
#                     json.dump(self.data, outfile, indent=2)
                
            else:
                page = "&Sort=SubmissionTime:desc&Limit=100&Offset={}".format(offset * 100)
                self.url = prefix + filter_id + filter_ratings + filter_time + page
#                 self.file_path = folder_path+id_+"_{}.json".format(offset)
#                 self.file_path = folder_path+id_+"_0{}.json".format(offset)
                self.browser.get(self.url)
                self.data = json.loads(self.browser.find_element_by_xpath("/html/body/pre").text)
                with open(self.file_path, "w") as outfile:
                    json.dump(self.data, outfile, indent=2)
                if self.data["TotalResults"] - 100 * (offset + 1) <= 0:
                    break