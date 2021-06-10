import argparse
import os

from chapter_extraction.utils import filesToSoup, get_soup_dictionary, match_soup, get_part_soup, get_chapters_html

def convert(file, out_path, chapter_num=24, chapters=None, combine=True):
    """
    To convert file into chapters using menu
    :param file: str, original file path
    :param out_path: str, file output path
    :param chapter_num: int, number of chapters to extract
    :param chapters: json, chapter information, optional
    :param combine: boolen, combine target chapters into one html, optional
    :return:
    """
    filename = os.path.basename(file)
    soup = filesToSoup(file, out_path)

    # get dictionary from soup
    file_dictionary, para_id = get_soup_dictionary(soup, chapter_num)
    # print(file_dictionary)

    dic, li = match_soup(para_id, file_dictionary, soup)

    get_part_soup(soup, dic, li)

    if chapters is not None:
        get_chapters_html(soup, dic, chapters, combine, out_path)

    if not combine:
        with open(os.path.join(out_path, (filename + ".html")), "w") as temp:
            temp.write(str(soup))
            temp.close()
    else:
        for chapter in dic:
            para = [p for p in soup.find_all() if p.name in ['table', 'p']]
            out_file = os.path.join(out_path, (filename + "_" + chapter + ".html"))
            with open(out_file, "w") as temp:
                target = [p for p in para if p["chapter"] == chapter]
                for p in target:
                    lines = [line for line in p.find_all() if line.name in ['line']]
                    for line in lines:
                        del line['style']

                    del p['style']
                target = [str(p) for p in target]
                temp.write(''.join(target))
                temp.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--fileDir", type=str, help="path to file dir", required=True)
    parser.add_argument("--out_path", type=str, help="path to output dir", required=True)
    parser.add_argument("--chapter_num", type=int, help="number of chapters to extract", required=True)
    parser.add_argument("--chapters", type=str, help="chapter information", required=False, default=None)
    parser.add_argument("--combine", type=bool, help="combine target chapters into one html", required=False, default=True)
    args = parser.parse_args()

    file_dir = args.fileDir
    out_path = args.out_path
    chapter_num = args.chapter_num
    chapters = args.chapters
    combine = args.combine

    files = os.listdir(file_dir)
    for file in files:
        filepath = os.path.join(file_dir, file)
        convert(filepath, out_path, chapter_num, chapters, combine)
        print("[INFO] Finish ", file)





