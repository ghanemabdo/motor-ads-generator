#!/usr/bin/env python3

'''Given car url, download its resources'''
__author__ = "Abdurrahman Ghanem"


import sys
import os
from lxml import html
import requests
import json
import datetime


def extract_info(url):
    page = requests.get(url)
    tree = html.fromstring(page.content)

    milage = tree.xpath("(//div[contains(@class,'h-carBestDetails') and contains(@class,'clearfix')]/div[@class='item'])[2]/text()")
    milage = milage[0].strip()

    model = tree.xpath('//h2[@class="h-carName"]/text()')
    model = model[0].strip()

    price = tree.xpath('//span[@class="h-carPrice"]/text()')
    price = price[0].strip()

    tels = tree.xpath('//a/@href')

    tel_nums = []

    for tel in tels:
        if tel.startswith("tel:"):
            tel_nums.append(tel.replace("tel:", ""))

    info_dict = {}

    info_dict["mileage"] = milage
    info_dict["model"] = model
    info_dict["price"] = price.replace("QAR", "").strip()
    if len(tel_nums) > 0:
        info_dict["tel"] = tel_nums[0]

    print(info_dict)

    return info_dict


def save_info(info_dict, res_dir):
    filename = "/data.json"

    with open(res_dir + filename, "w", encoding='utf-8') as json_file:
        data = json.dumps(info_dict, ensure_ascii=False)
        json_file.write(data)


def extract_imgs(url):
    page = requests.get(url)
    tree = html.fromstring(page.content)
    imgs = tree.xpath('//img[@class="img-responsive"]/@src')
    fixed_img_urls = []

    for img in imgs:
        fixed_img_urls.append(img.replace("thumb/", "o_"))

    print(fixed_img_urls)

    return fixed_img_urls


def download_imgs(img_urls, out_dir):
    if not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    counter = 1
    for url in img_urls:
        f = open(out_dir + "/" + str(counter) + ".jpg", 'wb')
        print("downloading image " + url)
        f.write(requests.get(url).content)
        f.close()
        counter += 1


def download_url(url):
    out_dir = url.split("/")
    if len(out_dir[len(out_dir) - 1]) > 0:
        out_dir = out_dir[len(out_dir) - 2]
    else:
        out_dir = out_dir[len(out_dir) - 3]

    out_dir = datetime.datetime.now().strftime("%Y/%m/%d/") + out_dir

    if os.path.exists(out_dir):
        return out_dir

    imgs = extract_imgs(url)
    download_imgs(imgs, out_dir)

    if "/en/" in url:
        page_info_en = extract_info(url)
        page_info_ar = extract_info(url.replace("/en/", "/ar/"))
    elif "/ar/" in url:
        page_info_ar = extract_info(url)
        page_info_en = extract_info(url.replace("/ar/", "/en/"))

    page_info = {}
    page_info["ar"] = page_info_ar
    page_info["en"] = page_info_en

    save_info(page_info, out_dir)

    return out_dir

##MAIN##
if __name__ == "__main__":
    '''read the index file from the input directory and generate the corresponding ad images'''

    if len(sys.argv) < 2:
        print("You must enter the resources directory")
        sys.exit(1)

    car_url = sys.argv[1]

    download_url(car_url)
