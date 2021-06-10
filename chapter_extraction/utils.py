# FC file processing utilities
import difflib
import ntpath
import os
import re
import unicodedata

import fitz
import numpy as np

from bs4 import BeautifulSoup

from similarity.weighted_levenshtein import WeightedLevenshtein
from similarity.weighted_levenshtein_test import CharSub


def check_bad_char(char):
    category = unicodedata.category(char)
    is_bad_char = ((category == 'Co') or (ord(char) == 65533))
    return is_bad_char


def check_by_iou(box_list, page_box, iou_thresh):
    err = ""
    boxes = np.array(box_list)
    x1 = boxes[:, 0]
    y1 = boxes[:, 1]
    x2 = boxes[:, 2]
    y2 = boxes[:, 3]
    filter = (x1 > page_box[2]) + (y1 > page_box[3]) + (x2 <= x1) + (y2 <= y1)
    if filter.sum() > 0:
        err += f"Filter illegal box coordinates"

    boxes = boxes[np.logical_not(filter)]
    boxes[:, 0:4][boxes[:, 0:4] < 0] = 0
    boxes[:, 2][boxes[:, 2] >= page_box[2]] = page_box[2] - 1
    boxes[:, 3][boxes[:, 3] >= page_box[3]] = page_box[3] - 1

    x1 = boxes[:, 0]
    y1 = boxes[:, 1]
    x2 = boxes[:, 2]
    y2 = boxes[:, 3]
    area = (x2 - x1 + 1) * (y2 - y1 + 1)
    page_area = page_box[2] * page_box[3]

    xx1 = np.maximum(page_box[0], x1)
    yy1 = np.maximum(page_box[1], y1)
    xx2 = np.minimum(page_box[2], x2)
    yy2 = np.minimum(page_box[3], y2)
    w = np.maximum(0.0, xx2 - xx1 + 1)
    h = np.maximum(0.0, yy2 - yy1 + 1)
    inter = w * h
    iou = inter / (page_area + area - inter)

    if (iou > iou_thresh).sum() > 0:
        return True, err  # is a image pdf
    else:
        return False, err  # not a image pdf


def detect_pdf_type(pdf_path, max_images=1000):
    """return True of the pdf is searchable"""

    flag = 0
    doc = fitz.open(pdf_path)
    for idx, page in enumerate(doc):

        if (float(flag) / doc.pageCount) >= 0.5:
            return False

        page_text = page.getText("")
        remove_spaces_text = "".join(page_text.split())
        total_bad_char = sum([check_bad_char(char) for char in remove_spaces_text])

        if len(remove_spaces_text) and float(total_bad_char) / len(remove_spaces_text) > 0.9:
            flag += 1
            continue

        if len(doc) > 1 and idx == 0:  # skip first page
            continue

        if page.rotation != 0:
            page.setRotation(0)  # fix coordinate inconsistency issue when page.rotation != 0

        page_box = page.rect
        # get images from text dict
        blocks = page.getText("dict")['blocks']
        boxes = [block['bbox'] for block in blocks if block["type"] == 1]

        # get images from image list
        xref = page.getImageList(full=True)
        image_boxes = []
        if len(xref) > max_images:
            flag += 1
            continue
        for img in xref:
            try:
                box = page.getImageBbox(img)
            except ValueError:
                item = list(img)
                item[-1] = 0
                box = page.getImageBbox(item)
            image_boxes.append(box)

        if len(boxes) > 0:
            iou_result, err = check_by_iou(boxes, page_box, 0.6)
            text_boxes = [block['bbox'] for block in blocks if block["type"] == 0]
            boxes_area = sum([(i[2] - i[0]) * (i[3] - i[1]) for i in boxes])
            text_area = sum([(i[2] - i[0]) * (i[3] - i[1]) for i in text_boxes])
            if boxes_area > text_area * 2 or iou_result:
                flag += 1
                continue

        if len(image_boxes) > 0:
            iou_result, err = check_by_iou(image_boxes, page_box, 0.6)
            if iou_result:
                flag += 1
                continue

    return (float(flag) / doc.pageCount) < 0.5


def title_tokenizer(text, language):
    if language == "Chinese":
        # 只保留中文字符
        if "<p>" in text or "<line>" in text:
            inner_text = BeautifulSoup(text).getText()
            result = re.findall(r'[\u4e00-\u9fa5]', str(inner_text))
        else:
            result = re.findall(r'[\u4e00-\u9fa5]', str(text))
    elif language == "English":
        if "<p>" in text or "<line>" in text:
            inner_text = BeautifulSoup(text).getText()
            result = re.findall(r'[a-z]|[A-Z]', str(inner_text))
        else:
            result = re.findall(r'[a-z]|[A-Z]', str(text))
    result = "".join(result)
    result = result.replace("和", "")
    result = result.replace("与", "")
    result = result.replace("或", "")
    result = result.replace("的", "")
    return result


def get_same_char_num(config_chapter, current_chapter):
    if current_chapter == '' or current_chapter is None:
        return 0

    return difflib.SequenceMatcher(None, config_chapter, current_chapter).quick_ratio()


def find_min_string(chapters, current_file_list):
    """
    :param chapters: title in config, only true
    :param current_file_list:  title in current file
    :return:
    """
    # # 默认cover 保留
    # extract_chapters = ["cover"]
    extract_chapters = []
    for key_string, value in chapters.items():
        if value:
            key_string_tokenize = title_tokenizer(key_string)
            same_char_num_s = [get_same_char_num(key_string_tokenize, title_tokenizer(i)) for i in current_file_list]
            max_mun = max(same_char_num_s)
            index = same_char_num_s.index(max_mun)
            if max_mun < 0.25:
                print("[INFO] Current file don't have chapter ", key_string)
                return None, None
            else:
                extract_chapters.append(current_file_list[index])

    return extract_chapters


def get_chapters_html(soup, dic, chapters, combine, out_path):
    current_file_list = dic
    extract_chapters = find_min_string(chapters, current_file_list)
    para = [p for p in soup.find_all() if p.name in ['img', 'table', 'p']]
    for p in para:
        if p['chapter'] not in extract_chapters or len(p.get_text().strip()) == 0:
            if "style" in p.attrs:
                p['style'] += ";display:none;"
            else:
                p['style'] = "display:none;"


# docx to soup
def docxTosoup(filePath, output_dir_parent, timeout=None):
    basename = ntpath.basename(filePath)
    output_file = basename.replace(".docx", ".html")
    output_file = output_file.replace(".doc", ".html")
    output_dir = output_dir_parent + "/docxDir/"
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    outhtml = os.path.join(output_dir, output_file)
    os.system('unoconv -f html -o' + " " + outhtml + " " + filePath)
    with open(outhtml, 'r') as temp:
        html = temp.read()
        temp.close()
        soup = BeautifulSoup(html, "html.parser")
    return soup


# pdf to soup
def pdfTosoup(filePath, output_dir_parent, timeout=None):
    basename = ntpath.basename(filePath)
    output_file = basename.replace(".pdf", ".html")
    output_dir = output_dir_parent + "/pdfDir/"
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    outhtml = os.path.join(output_dir, output_file)
    print(outhtml)
    os.system('unoconv -f html -o' + " " + outhtml + " " + filePath)
    with open(outhtml, 'r') as temp:
        html = temp.read()
        temp.close()
        soup = BeautifulSoup(html, "html.parser")
    return soup


# html to soup
def htmlTosoup(file_path):
    with open(file_path, "r") as temp:
        soup = BeautifulSoup(temp.read())
        temp.close()
    return soup


def filesToSoup(filePath, output_dir_parent):
    if not os.path.exists(output_dir_parent):
        os.mkdir(output_dir_parent)

    filename = ntpath.basename(filePath)
    type = filename.split(".")[-1]
    print(type)
    if type == "docx" or type == "doc":
        soup = docxTosoup(filePath, output_dir_parent)
        return soup
    elif type == "pdf":
        if detect_pdf_type(filePath):
            soup = pdfTosoup(filePath, output_dir_parent)
        else:
            raise ValueError("Sorry, The template doesn't support imagae PDFs currently.")
        return soup
    elif type == "html":
        soup = htmlTosoup(filePath)
        return soup
    else:
        raise ValueError("Sorry, The template doesn't support ." + type + " currently.")


# tokeinze text, only keep chinese character
def content_tokenizer(text, language):

    if language == "Chinese":
        # 只保留中文字符
        if "<p>" in text or "<line>" in text:
            inner_text = BeautifulSoup(text).getText()
            result = re.findall(r'[\u4e00-\u9fa5]', str(inner_text))
        else:
            result = re.findall(r'[\u4e00-\u9fa5]', str(text))
    if language == "English":
        if "<p>" in text or "<line>" in text:
            inner_text = BeautifulSoup(text).getText()
            result = re.findall(r'[a-z]|[A-Z]', str(inner_text))
        else:
            result = re.findall(r'[a-z]|[A-Z]', str(text))
    result = "".join(result)
    return result


def find_soup_menu(para, language):
    for index in range(len(para)):
        text = para[index].get_text()
        text = content_tokenizer(text, language)
        if language == "Chinese":
            if "目" == text:
                for j in range(index, min(index + 10, len(para))):
                    next_text = content_tokenizer(para[j].get_text(), language)
                    if next_text == "":
                        continue
                    elif next_text == "录":
                        return para[j]['p_id']
            elif "目录" in text:
                return index
            elif index == len(para) - 1:
                raise ValueError("您选择了错误的模版，请使用通用文本进行解析！")
        elif language == "English":
            if "contents" in text.lower():
                return index
            elif index == len(para) - 1:
                raise ValueError("Wrong template！")



def get_title(text):
    if "第" in text:
        text_list = text.split("第")[1:]
        new_text = [re.sub(".部分|..部分|...部分", "", i) for i in text_list]
        new_text = [re.sub(".节|..节|...节", "", i) for i in new_text]
        new_text = [re.sub("\s+", "", i) for i in new_text]
        new_text = [re.sub("十|一|二|三|四|五|六|七|八|九", "", i) for i in new_text]
        return new_text
    else:
        tmp = "".join(re.sub(".部分|..部分|...部分", "", text))
        tmp = "".join(re.sub(".节|..节|...节", "", tmp))
        tmp = "".join(re.sub("\s+", "", tmp))
        tmp = "".join(re.sub("十|一|二|三|四|五|六|七|八|九", "", tmp))
        return [tmp]


def get_soup_dictionary(soup, chapter_num, language):
    file_dictionary = []
    num = 0
    para = [p for p in soup.find_all() if p.name in ['img', 'table', 'p']]
    x = find_soup_menu(para, language)
    for k in range(x + 1, len(para)):
        text = content_tokenizer(para[k].get_text(), language)
        para[k]['chapter'] = 'cover'
        if text != "" and "\x0c" not in text:
            new_text = get_title(text)
            if new_text == ['']:
                continue
            else:
                file_dictionary += new_text
            num += 1
            if num > chapter_num:
                num += 1
                break
    return file_dictionary, k + 1


def match_dic_soup(file_dictionary, p, language):
    match = None
    a = WeightedLevenshtein(character_substitution=CharSub())
    original_sentence = p.get_text()
    sentence = content_tokenizer(original_sentence, language)
    new_text = "".join(get_title(sentence))

    for i in range(0, len(file_dictionary)):
        # pattern_1 = dictionary[i]+file_dictionary[i]
        length = - int(len(file_dictionary[i]))

        title = file_dictionary[i]

        tmp = "".join(re.sub(".部分|..部分|...部分", "", file_dictionary[i]))
        tmp = "".join(re.sub("第", "", tmp))
        tmp = "".join(re.sub(".节|..节|...节", "", tmp))
        tmp = "".join(re.sub("\s+", "", tmp))
        tmp = "".join(re.sub("十|一|二|三|四|五|六|七|八|九", "", tmp))

        if tmp == sentence[length:] and "本" + tmp != sentence[length - 1:] and "的" + tmp != sentence[length - 1:]:
            last_char = original_sentence.strip()[-1]
            if not last_char in [";", "；", "。", "\"", "”"]:
                match = title
                file_dictionary.remove(title)
                break
        elif abs(len(new_text) - len(tmp)) >= 3:
            continue
        elif a.distance(sentence, tmp) <= 1 or a.distance(new_text, tmp) <= 1:
            match = title
            file_dictionary.remove(title)
            break
        else:
            continue
    return match, file_dictionary


# 删掉相同的内容（将页眉误认为目录之一）
def delete_duplicate(dic, li):
    new_dic = []
    new_li = []
    for i in range(0, len(dic)):
        if dic[i] not in new_dic:
            new_dic.append(dic[i])
            new_li.append(li[i])
    return new_dic, new_li


def match_soup(para_id, file_dictionary, soup, language):
    dic = []
    li = []
    para = [p for p in soup.find_all() if p.name in ['img', 'table', 'p']]
    for i in range(para_id, len(para)):
        if len(file_dictionary) > 0:
            result, file_dictionary = match_dic_soup(file_dictionary, para[i], language)
            if result != None:
                dic.append(result)
                li.append(i)

    dic, li = delete_duplicate(dic, li)

    return dic, li


def get_part_soup(soup, dic, li):
    para = [p for p in soup.find_all() if p.name in ['img', 'table', 'p']]
    for index in range(li[0]):
        para[index]['chapter'] = "cover"

    for i in range(0, len(li) - 1):
        beginning = li[i]
        end = li[i + 1]
        for index in range(beginning, end):
            para[index]['chapter'] = dic[i]

    for index in range(li[-1], len(para)):
        para[index]['chapter'] = dic[-1]
