#!/usr/bin/env python3

'''combine multiple images to build ads images to be posted on social media'''
__author__ = "Abdurrahman Ghanem"


import sys
import os
from shutil import copyfile
import json
from resources_crawler import download_url
from PIL import Image, ImageFont, ImageDraw
import unicodedata as ud
import arabic_reshaper
from bidi.algorithm import get_display
import datetime


def is_empty_line(line):
    if len(line.strip()) == 0:
        return True
    else:
        return False


latin_letters = {}


def is_latin(uchr):
    try: return latin_letters[uchr]
    except KeyError:
        return latin_letters.setdefault(uchr, 'LATIN' in ud.name(uchr))


def only_roman_chars(unistr):
    return all(is_latin(uchr) for uchr in unistr if uchr.isalpha())


def fix_arabic_text(text):
    if only_roman_chars(text):
        return text

    return get_display(arabic_reshaper.reshape(text))


def get_max_font_size(font_file, text, fit_size):
    font_size = 8
    font = ImageFont.truetype(font_file, font_size)
    width, height = font.getsize(text)
    while width < fit_size[0] and height < fit_size[1]:
        font_size += 1
        font = ImageFont.truetype(font_file, font_size)
        width, height = font.getsize(text)

    return ImageFont.truetype(font_file, font_size - 1)


def get_text_centered_position(font_size, fit_size, x , y):
    new_x = x + ((fit_size[0] - font_size[0]) / 2)
    new_y = y + ((fit_size[1] - font_size[1]) / 2)

    return (new_x , new_y)


def load_json(jsonfile):
    if os.path.exists(jsonfile):
        with open(jsonfile, "r") as jsonf:
            resources_dict = json.load(jsonf)
            return resources_dict


def read_index(idx_file):
    return load_json(idx_file)


def read_descriptor(desc_file):
    return load_json(desc_file)


def download_resources(urls):
    out_folders = []
    for url in urls:
        out_folders.append(download_url(url))

    return out_folders


def get_urls(urls_file):
    urls = []
    with open(urls_file, "r") as f:
        for url in f:
            urls.append(url)

    return urls


def open_template(temp_name):
    tn = temp_name
    if "templates/" not in temp_name:
        tn = "templates/" + temp_name
    if os.path.exists(tn):
        img = Image.open(tn)
        img.load()
        return img


def open_template_overlay(temp_name):
    tn = temp_name
    if "templates/" not in temp_name:
        tn = "templates/" + temp_name
    if os.path.exists(tn):
        toimg = Image.open(tn)
        toimg.load()
        return toimg


def crop_img_center(img , new_width , new_height):
    width, height = img.size
    if new_width <= width and new_height <= height:
        left = (width - new_width) / 2
        upper = (height - new_height) / 2
        right = left + new_width
        lower = upper + new_height
        box = (left, upper, right, lower)
        return img.crop(box)
    else:
        return img


def paste_img(template , to_paste_img , x , y):
    box = (x, y, x + to_paste_img.size[0], y + to_paste_img.size[1])
    if to_paste_img.mode == "RGBA":
        template.paste(to_paste_img, box, to_paste_img)
    else:
        template.paste(to_paste_img, box)
    return template


def add_img_to_template(post_folder, template, img_desc):
    post_img = Image.open(post_folder + img_desc["file"])
    post_img = crop_img_center(post_img, img_desc["crop_width"], img_desc["crop_height"])
    post_img = post_img.resize((img_desc["fit_width"], img_desc["fit_height"]), Image.ANTIALIAS)
    return paste_img(template, post_img, img_desc["x"], img_desc["y"])


def draw_text_to_img(img, text, font_file, font_size, color, x, y, fit_size):
    draw = ImageDraw.Draw(img)
    if os.path.exists(font_file):
        font = get_max_font_size(font_file, text, fit_size)
        draw.rectangle(((x,y), (x + fit_size[0], y + fit_size[1])), fill="yellow")
        x, y = get_text_centered_position(font.getsize(text), fit_size, x, y)
        draw.text((x, y), text, tuple(color), font=font)
    return img


def get_post_text(post_data_dict, text_dict):
    if "lang" in text_dict and text_dict["lang"] in post_data_dict:
        lang_dict = post_data_dict[text_dict["lang"]]
        if "text" in text_dict and text_dict["text"] in lang_dict:
            text = lang_dict[text_dict["text"]]
            text = fix_arabic_text(text)
            return text

    return ""


def render_text_to_img(template, text_desc, img_texts, post_folder):

    if "post_folder" in text_desc:
        pf = text_desc["post_folder"] + "/"
        img_texts = load_json(post_folder + pf.replace("//", "/") + "data.json")
    if img_texts is None:
        return

    text = get_post_text(img_texts, text_desc)
    font_file = text_desc["font_file"]
    font_color = bytes.fromhex(text_desc["font_color"][1:])
    font_size = text_desc["font_size"]
    x = text_desc["x"]
    y = text_desc["y"]
    max_width = text_desc["width"]
    max_height = text_desc["height"]
    return draw_text_to_img(template, text, font_file, font_size, font_color, x, y, (max_width, max_height))


def images_generated_before(desc_file, desc_dict, post_folder):
    for ext in desc_dict["save_formats"]:
        f = os.path.basename(desc_file)
        f, e = os.path.splitext(f)
        if os.path.exists(post_folder + f + ext) is False:
            return False
    return True


def create_post_img(desc_dict, post_folder):
    template = open_template(desc_dict["template"])
    template_overlay = open_template_overlay(desc_dict["template_overlay"])

    if template is None or template_overlay is None:
        return False

    for img_desc in desc_dict["images"]:
        if os.path.exists(post_folder + img_desc["file"]):
            add_img_to_template(post_folder, template, img_desc)
        else:
            return False

    template = paste_img(template, template_overlay, 0, 0)

    posts = set()
    for img_desc in desc_dict["images"]:
        path_comps = img_desc["file"].split("/")
        if len(path_comps) > 1:
            posts.add(path_comps[0])

    img_texts = load_json(post_folder + "data.json")

    if img_texts is not None or len(posts) > 0:
        for text_desc in desc_dict["captions"]:
            render_text_to_img(template, text_desc, img_texts, post_folder)

    return template


def save_img(img, post_folder, fname, formats):
    if os.path.exists(post_folder):
        for ext in formats:
            if img is not None:
                img.save(post_folder + fname + "." + ext)


def image_exists(img_desc, post_folder, ext=".jpg"):
    f = os.path.basename(img_desc)
    f, e = os.path.splitext(f)

    return os.path.exists(post_folder + f + ext)


def copy_img_if_exists(img_desc, post_folder, video_name, fname):
    f = os.path.basename(img_desc)
    f, e = os.path.splitext(f)

    if image_exists(img_desc, post_folder):
        copyfile(post_folder + f + ".jpg", post_folder + video_name + "/" + fname + ".jpg")
        return True
    else:
        return False


def copy_descriptor_file(desc_name, dest_dir):
    if os.path.exists("descriptors/" + desc_name):
        os.makedirs(dest_dir, exist_ok=True)
        copyfile("descriptors/" + desc_name, dest_dir + desc_name)


def save_video(imgs_path, video_path, img_duration):
    command = "ffmpeg -r " + str(img_duration) + " -i " + imgs_path + "%d" + ".jpg -vcodec mpeg4 -y " + \
              video_path + ".mp4"
    os.system(command)


def create_post_video(desc_dict, post_folder):
    if "videos" in desc_dict:
        counter = 0
        for video in desc_dict["videos"]:
            if not os.path.exists(post_folder + video["name"] + "/"):
                os.mkdir(post_folder + video["name"] + "/")
            for img_desc in video["images"]:
                copy_descriptor_file(img_desc, post_folder)
                if not copy_img_if_exists(img_desc, post_folder, video["name"], str(counter)):
                    img_dict = load_json(post_folder + img_desc)
                    img = create_post_img(img_dict, post_folder)
                    if img is False:
                        continue
                    f, e = os.path.splitext(img_desc)
                    save_img(img, post_folder + video["name"] + "/", str(counter), ["jpg"])
                counter += 1
            save_video(post_folder + video["name"] + "/", post_folder + video["name"] + "/" + video["name"], video["image_duration"])




##MAIN##
if __name__ == "__main__":
    '''read the index file from the input directory and generate the corresponding ad images'''

    if len(sys.argv) < 2:
        print("You must enter the resources directory")
        sys.exit(1)

    urls_file = sys.argv[1]

    out_dirs = download_resources(get_urls(urls_file))

    index_file = "index.json"
    if len(sys.argv) > 3:
        index_file = sys.argv[3]

    index_dict = read_index(index_file)

    date_folder = datetime.datetime.now().strftime("%Y/%m/%d/")

    for post_folder in index_dict:
        for desc_file in index_dict[post_folder]:
            post_folder_with_date = date_folder + post_folder.replace(".", "")
            copy_descriptor_file(desc_file, post_folder_with_date)
            desc_dict = read_descriptor(post_folder_with_date + desc_file)
            filename, ex = os.path.splitext(desc_file)
            if images_generated_before(desc_file, desc_dict, post_folder_with_date) is False:
                post_img_combined = create_post_img(desc_dict, post_folder_with_date)
                if post_img_combined is not False:
                    save_img(post_img_combined, post_folder_with_date, filename, desc_dict["save_formats"])

            create_post_video(desc_dict, post_folder_with_date)
