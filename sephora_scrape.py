#!/usr/bin/env python
# coding: utf-8

# In[3]:


from bs4 import BeautifulSoup
from random import randint, shuffle
from time import sleep
import re
import pandas as pd
import json
import requests
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import os
import numpy as np


# In[1]:


def get_products(soup):

    prefix_url = "https://www.sephora.com"

    try:
        product_json = soup.find_all(attrs={"type": re.compile("text/json")})
        product_json = json.loads(product_json[0].text)
    except:
        print(filename, " - download unsuccessful")

    product_list = []

    for i in product_json:
        for key, val in i["props"].items():
            if key == "products":
                if type(val) == list:
                    for product in val:

                        product_dict = {}  #each product

                        product_dict["brand_name"] = product["brandName"]

                        product_dict["product_ref"] = product["productId"]

                        product_dict["product_item"] = product["currentSku"][
                            "skuId"]

                        product_dict["product_name"] = product["displayName"]

                        product_dict["product_price"] = product["currentSku"][
                            "listPrice"]

                        product_dict["product_image"] = prefix_url + product[
                            "currentSku"]["skuImages"]["image450"]

                        product_dict[
                            "product_link"] = prefix_url + product["targetUrl"]

                        product_list.append(product_dict)

    if len(product_list) != 0:
        return product_list

    else:

        if len(soup.find_all("a", href=re.compile("/product/"))) == 0:
            return product_list

        else:
            for tag in soup.find_all("a", href=re.compile("/product/")):

                product_dict = {}  #each product

                product_dict["brand_name"] = tag.find(
                    attrs={
                        "data-at": re.compile("sku_item_brand")
                    }).get_text(strip=True).replace(" NEW", "")
                try:
                    product_dict["product_ref"] = tag.attrs["data-uid"].split(
                    )[0]
                except:
                    product_dict["product_ref"] = np.nan

                try:
                    product_dict["product_item"] = tag.attrs["data-uid"].split(
                    )[-1]
                except:
                    product_dict["product_item"] = np.nan

                try:
                    product_dict["product_name"] = tag.find(
                        attrs={
                            "data-at": re.compile("sku_item_name")
                        }).get_text(strip=True)
                except:
                    product_dict["product_name"] = np.nan

                try:
                    product_dict["product_price"] = tag.find(
                        attrs={
                            "data-at": re.compile("sku_item_price_list")
                        }).get_text(strip=True)
                except:
                    product_dict["product_price"] = np.nan

                try:
                    product_dict["product_image"] = prefix_url + tag.find(
                        attrs={
                            "src": re.compile("/productimages/")
                        }).get("src")
                    if product_dict["product_item"] is np.nan:
                        item_pattern = re.compile("s[0-9]+")
                        product_dict["product_item"] = item_pattern.findall(
                            product_dict["product_image"])[0].strip("s")
                except:
                    product_dict["product_image"] = np.nan

                try:
                    product_dict[
                        "product_link"] = prefix_url + tag.attrs["href"]
                    if product_dict["product_ref"] is np.nan:
                        ref_pattern = re.compile("P[0-9]+")
                        product_dict["product_ref"] = ref_pattern.findall(
                            product_dict["product_link"])[0]
                except:
                    product_dict["product_link"] = np.nan

                product_list.append(product_dict)

        return product_list


# In[5]:


def download_json(filename, folder_path):
    
    tag_remover = re.compile(
    '<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});|\r|\n')
    logo_remover = re.compile('\?.*')
    
    with open(folder_path + filename) as json_file:
        data = json.load(json_file)

    details_dict = {}

    details_dict["id"] = data["productId"]
    details_dict["name"] = data["displayName"]

    short_desc = data[
        "quickLookDescription"] if "quickLookDescription" in data else data[
            "shortDescription"]
    details_dict["short_desc"] = tag_remover.sub(" ", short_desc).strip()

    details_dict["long_desc"] = tag_remover.sub(
        " ", data["longDescription"]).strip()

    details_dict["item"] = data["currentSku"]["skuId"]
    details_dict["item_name"] = data["currentSku"][
        "skuName"] if "skuName" in data["currentSku"] else (
            data["currentSku"]["displayName"]).replace(
                data["currentSku"]["skuId"], "").strip()
    details_dict["list_price"] = float(
        data["currentSku"]["listPrice"].strip("$"))

    details_dict["variation"] = data["currentSku"]["variationTypeDisplayName"]

    if "regularChildSkus" in data:
        variants = []
        prices = []
        for i, sku in enumerate(data["regularChildSkus"]):
            variants.append({
                i + 1: {
                    "item":
                    sku["skuId"],
                    "item_name":
                    sku["skuName"]
                    if "skuName" in data["regularChildSkus"][i] else np.nan,
                    "list_price":
                    float(sku["listPrice"].strip("$"))
                }
            })
            prices.append(float(sku["listPrice"].strip("$")))

    details_dict[
        "variants"] = variants if "regularChildSkus" in data else np.nan
    details_dict["price_low"] = min(
        prices) if "regularChildSkus" in data else details_dict["list_price"]
    details_dict["price_high"] = max(
        prices) if "regularChildSkus" in data else details_dict["list_price"]

    details_dict["is_limited_edition"] = int(
        data["currentSku"]["isLimitedEdition"])
    details_dict["is_natural_organic"] = int(
        data["currentSku"]["isNaturalOrganic"])
    details_dict["is_natural_sephora"] = int(
        data["currentSku"]["isNaturalSephora"])

    details_dict["rating"] = data["rating"] if "rating" in data else np.nan
    details_dict["review_count"] = data["reviews"] if "reviews" in data else 0
    details_dict[
        "user_favorites"] = data["lovesCount"] if "lovesCount" in data else 0

    if "parentCategory" in data:
        category_1 = data["parentCategory"][
            "displayName"] if "parentCategory" in data else "nan"
        category_2 = data["parentCategory"]["parentCategory"][
            "displayName"] if (
                "parentCategory" in data["parentCategory"]) else "nan"
        category_3 = data["parentCategory"]["parentCategory"][
            "parentCategory"]["displayName"] if (
                "parentCategory" in data["parentCategory"] and "parentCategory"
                in data["parentCategory"]["parentCategory"]) else "nan"

        category_id_1 = data["parentCategory"][
            "categoryId"] if "parentCategory" in data else "nan"
        category_id_2 = data["parentCategory"]["parentCategory"][
            "categoryId"] if "parentCategory" in data[
                "parentCategory"] else "nan"
        category_id_3 = data["parentCategory"]["parentCategory"][
            "parentCategory"]["categoryId"] if (
                "parentCategory" in data["parentCategory"] and "parentCategory"
                in data["parentCategory"]["parentCategory"]) else "nan"

        category_id = [category_id_1, category_id_2, category_id_3]
        category = [category_1, category_2, category_3]
        
        details_dict["categories"] = dict(
            zip([id_ for id_ in category_id if id_!="nan"],
                [cat for cat in category if cat!="nan"]))

    else:
        details_dict["categories"] = np.nan

    details_dict["url"] = data["fullSiteProductUrl"]
    details_dict["image_url"] = logo_remover.sub("","https://www.sephora.com" + data["currentSku"][
        "skuImages"]["image1500"])
    
    details_dict["ingredients"] = tag_remover.sub(
        " ", data["currentSku"]["ingredientDesc"]).strip(
        ) if "ingredientDesc" in data["currentSku"] else np.nan

    details_dict["suggested_usage"] = tag_remover.sub(
        " ",
        data["suggestedUsage"]).strip() if "suggestedUsage" in data else np.nan

    details_dict["brand_name"] = data["brand"]["displayName"]
    details_dict["brand_id"] = data["brand"]["brandId"]
    details_dict["brand_long"] = data["brand"]["longDescription"]

    return details_dict


# In[4]:


def get_image(url, filename, folder_path):
    r = requests.get(url, allow_redirects=True)
    if r.status_code==200:
        open(folder_path+filename, 'wb').write(r.content)
    else:
        print("Error: opening image url for product {}".format(filename.replace(".png", "")))
    sleep(3)


# In[2]:


def close_country_box(browser):
    try:
        browser.find_element_by_xpath("//*[@id='MediaModal']/button").click()
        return browser
    except:
        return browser


def close_login_box(browser):
    try:
        browser.find_element_by_xpath("//*[@id='modalDialog']/button").click()
        return browser
    except:
        return browser


def view_300(browser):
    try:
        if browser.find_element_by_class_name("css-1qizhe3").text.endswith("View all"):
            browser.find_element_by_class_name("css-1qizhe3").send_keys("View all")
            sleep(1)
            close_country_box(browser)
            close_login_box(browser)
            close_country_box(browser)
            scroll_to_bottom(browser, 5)
            sleep(1)
            close_country_box(browser)
            close_login_box(browser)
            close_country_box(browser)
            sleep(1)
            return browser
    except:
        return browser
        
        
def next_page(browser):
    try:
        if browser.find_element_by_class_name("css-4ktkov").get_attribute("aria-label")=="Next":
            browser.find_element_by_class_name("css-4ktkov").click()
            sleep(1)
            close_country_box(browser)
            close_login_box(browser)
            close_country_box(browser)
            scroll_to_bottom(browser, 5)
            sleep(1)
            close_country_box(browser)
            close_login_box(browser)
            close_country_box(browser)
            sleep(1)
            return browser
    except:
        return browser

    
def scroll_to_bottom(browser, x=20):
    sleep(1)
    close_country_box(browser)
    close_login_box(browser)
    close_country_box(browser)
    sleep(1)
    elem = browser.find_element_by_tag_name("body")
    no_of_pagedowns = x
    while no_of_pagedowns:
        elem.send_keys(Keys.PAGE_DOWN)
        sleep(0.5)
        close_country_box(browser)
        close_login_box(browser)
        close_country_box(browser)
        no_of_pagedowns -= 1
    return browser


# In[ ]:




