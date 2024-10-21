# from get_drug_list_info import (
#     get_all_data_with_indices,
#     write_to_csv,
#     write_to_csv_renal,
# )

from bs4 import BeautifulSoup
import pandas as pd
from html_sanitizer import Sanitizer
import html2text
import re


def get_all_pharma_html():
    df = pd.read_csv("working_example.csv", keep_default_na=False)
    values = df.values.tolist()
    return [(x[0], x[1], x[-1]) for x in values]


def consecutive_b_siblings(div):
    for b in div.find_all("b"):
        prev = b.previous_sibling
        if prev and prev.name == "b":
            return True
    return False


def merge_b_siblings(div):
    print(type(div))
    print("div string: \n", div.string)
    print(div)
    # all_b_tags = div.find_all("b")
    for b in div.find_all("b"):
        prev_b = b.previous_sibling
        if prev_b and prev_b.name == "b":
            prev_b.extend(b.contents)
            # b.string = prev.string + b.string
            # b.insert(0, prev.string)
            b.replace_with(prev_b)
    # if
    print("-------------")
    print(div)
    return div


def remove_last_period(pharma_forms):
    res = [f[:-1] if f[-1] == "." else f for f in pharma_forms]
    res = [r for r in res if r]
    return res


def get_all_bold(atc, index, markdown_text, pattern, exclusion_list):
    res = re.findall(pattern, markdown_text)
    res = [r for r in res if r not in exclusion_list]
    return res


def make_bold_weird(sub):
    res = "~".join(sub[2:-2])
    res = "~" + res + "~"
    # print(res)
    return res


def make_weird_bold(sub):
    res = sub.replace("~", "")
    res = "**" + res + "**"


def get_all_non_bold(atc, index, markdown_text, pattern, exclusion_list):
    bold_exclusion_list = ["**" + x + "**" for x in exclusion_list]
    weird_exclusion_list = [make_bold_weird(b) for b in bold_exclusion_list]
    altered_markdown = markdown_text
    for i in range(len(bold_exclusion_list)):
        altered_markdown = altered_markdown.replace(
            bold_exclusion_list[i], weird_exclusion_list[i]
        )
    split_text = [
        part.strip()
        for part in re.split(pattern, altered_markdown)
        if part and not re.match(pattern, "**" + part + "**")
    ]
    joined_split_text = "|||".join(split_text)
    for i in range(len(weird_exclusion_list)):
        joined_split_text = joined_split_text.replace(
            weird_exclusion_list[i], bold_exclusion_list[i]
        )
    res = joined_split_text.split("|||")
    # print(res)
    # res = re.split(pattern, res)
    # print(split_text)
    # res = split_text
    # for r in res:
    #     print(res)

    # res = re.sub(pattern, "", res)

    # print("----all markdown text")
    # print(markdown_text)
    # print("-----non-bold")
    # print(res)
    return res


sanitizer = Sanitizer()  # default configuration
h = html2text.HTML2Text()
h.ignore_links = True
h.body_width = 0

all_html = get_all_pharma_html()
all_pharma_forms = []
all_pharma_unbold_text = []
pattern = r"\*{2}(.*?)\*{2}"
exclusion_list = [
    "Obs.",
    "dexamfetaminsulfat",
    "dexamfetamin",
    "3",
    "Dosis nr. 1",
    "Dosis nr. 2",
    "1 brev A",
    "1 brev B",
    "1 brev",
    "Bemærk:",
    "rå opium",
    "10 mg morphin",
    ".",
]
# pattern = r"\*{2}(?!" + "|".join(exclusion_list) + ")(.*?)(?<!\s)\*{2}"
# should be like r"\*{2}(?!Obs\.|\.)(.*?)(?<!\s)\*{2}"
bold_examples = [8691, 8716, 9858, 7066, 7282, 10719]
# all_html = [h for h in all_html if h[0] in bold_examples]

for index, atc, html in all_html:
    sanitized_html = sanitizer.sanitize(html)
    markdown_text = h.handle(sanitized_html)
    annoying_commas = ["** ,**", "** , **"]
    for comma in annoying_commas:
        if comma in markdown_text:
            markdown_text = markdown_text.replace(comma, ",")
            print("ANNOYING COMMA WAS HERE: ", index, atc)
    pharma_forms = remove_last_period(
        get_all_bold(atc, index, markdown_text, pattern, exclusion_list)
    )
    pharma_non_bold = get_all_non_bold(
        atc, index, markdown_text, pattern, exclusion_list
    )

    if len(pharma_forms) != len(pharma_non_bold):
        # print(index, atc, pharma_forms)
        # print(pharma_non_bold)
        # print(markdown_text)
        # # print(*pharma_forms, sep="\n-")
        # print("-----------------------------")
        pass
    else:
        new_pharma_forms = []
        for bold, non_bold in zip(pharma_forms, pharma_non_bold):
            if "filmovertruk" in non_bold:
                # print("{}, {}, {}: {}".format(index, atc, bold, non_bold))
                new_pharma_forms.append(bold + ", filmovertrukne")
            if "sukkerovertruk" in non_bold:
                new_pharma_forms.append(bold + ", sukkerovertrukne")
            elif (
                "overtruk" in non_bold
                and "filmovertruk" not in non_bold
                and "sukkerovertruk" not in non_bold
            ):
                new_pharma_forms.append(bold + ", overtrukne")
                # print("{}, {}, {}: {}".format(index, atc, bold, non_bold))
            else:
                new_pharma_forms.append(bold)
        pharma_forms = new_pharma_forms
        for f in pharma_forms:
            print(f)
        # print(pharma_non_bold)
        # print(markdown_text)
        # # print(*pharma_forms, sep="\n-")
        # print("-----------------------------")
        # break
    # all_pharma_forms.extend(remove_last_period(pharma_forms))

# all_unique_pharma_forms = sorted(list(set(all_pharma_forms)))

# for i, (index, atc, html) in enumerate(all_html[:10]):
#     sanitized_html = sanitizer.sanitize(html)
#     markdown_text = h.handle(sanitized_html)
#     non_bold_text = get_all_non_bold(atc, index, markdown_text, pattern, exclusion_list)
# print(len(all_unique_pharma_forms))
# for unbold in non_bold_text:
# for f in all_unique_pharma_forms:
#     non_list = ["3", "enkeltdosis", "1 brev"]
#     # non_list = []
#     if f in non_bold_text and f not in non_list:
#         print(f"listindex: {i}, {index}, {atc}, pharma_form: {f}")
#         print("UNBOLD: \n", non_bold_text)
#         print("MARKDOWN: \n", markdown_text)
#         print("----------------------------------")
# print(non_bold_text)
# if "over" in non_bold_text:
#     print(f"listindex: {i}, {index}, {atc}, pharma_form: {f}")
#     print("NONBOLD")
#     print(non_bold_text)
#     print("------------------------------------")
