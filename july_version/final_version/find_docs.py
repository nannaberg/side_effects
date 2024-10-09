import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from datetime import datetime
import re

# from selenium import WebDriverException
import html2text
import os.path

# import unicode

# from get_drug_list_info import (
#     get_all_prioritized_data_with_or_without_indices,
#     write_to_csv,
#     get_all_docs_titles,
# )
import pandas as pd

doc_base_url = "https://produktresume.dk"


def get_search_url(atc, page_number=0):
    # https://produktresume.dk/AppBuilder/search?button=search&id=&page=1&q=%22C09DA01%22+OR+%22C+09+DA+01%22&type=&utf8=%E2%9C%93
    # base_url = "https://produktresume.dk/AppBuilder/search?utf8=%E2%9C%93&q="
    # end_base_url = "&button=search"
    base_url = "https://produktresume.dk/AppBuilder/search?button=search&id=&page={}&q=".format(
        page_number
    )
    end_base_url = "&type=&utf8=%E2%9C%93"
    # A11HA08, N05BA
    # "C+01+BD+01+" + OR + "C01BD01"
    indices = [0, 1, 3, 5]
    parts = [
        atc[i:j] for i, j in zip(indices, indices[1:] + [None]) if atc[i:j]
    ]  # for splitting up atc: A11HA08 -> A 11 HA 08 (might be how it is written in document)
    # if atc == "N05BA":
    #     print(parts)
    url = base_url + '("'
    for p in parts:
        url += p + "+"
    url += '"+OR+"' + atc + '")'
    url += end_base_url
    print("url: ", url)
    # url = base_url + "blabla" + end_base_url
    # "https://produktresume.dk/AppBuilder/rich_preview?id=4f9c340f54ddc4ab0d8019014066f1de&query=%22C09DA01%22+OR+%22C+09+DA+01%22&type=productresume&embedded=true"
    return url


def get_firefox_driver():
    options = Options()
    download_dir = "docs1/downloaded_doc_docx_files/"
    abs_download_dir = os.path.abspath(download_dir)

    # do not use default Downloads directory, use the directory that we give instead
    options.set_preference("browser.download.folderList", 2)
    #
    options.set_preference("browser.helperApps.alwaysAsk.force", False)

    # disabling download manager when download begins, ie turns of showing download progress
    options.set_preference("browser.download.manager.showWhenStarting", False)

    # popup window announcing download complete will not appear
    options.set_preference("browser.download.manager.showAlertOnComplete", False)

    # list of MIME types to save to disk without asking what to use to open the file -> disables download dialog box/tells Firefox to automayically download the files of the selected MIME types
    # .doc: application/msword
    # .docx: application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document
    options.set_preference(
        "browser.helperApps.neverAsk.saveToDisk",
        "application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )

    # determines the dir to download to
    options.set_preference("browser.download.dir", abs_download_dir)

    # to avoid the page actually opening in browser
    options.add_argument("-headless")

    # dom access even without images, css, etc being loaded
    options.page_load_strategy = "eager"

    # apparently necessary because it is snap firefox
    service = Service(executable_path="/snap/bin/geckodriver")

    return webdriver.Firefox(options=options, service=service)


# def handle_doc(date, title):
# def collect_titles_dates(elms, atc, drug_f):
#     res = []
#     for elm in elms:
#         elm_html = elm.get_attribute(
#             "outerHTML"
#         )  # gives exact HTML content of the element
#         soup = BeautifulSoup(elm_html, "lxml")
#         # print(soup.a.prettify())
#         title = soup.a.get_text()
#         date = soup.find("span", class_="field_values").get_text().strip()
#         # print("Whole title: ", title)
#         if not "," in title:
#             print(
#                 "\t{}, {} -- TITLE: {} HAS NO COMMA, SO IT IS IGNORED: ".format(
#                     atc, drug_f, title
#                 )
#             )
#             continue
#         web_f = title.split(",", 1)[1]
#         if all(f in web_f for f in drug_f.split(",")):
#             found += 1
#         res.append((date, title))
#         return res
# print(text)


# def click_next(driver):
#     driver.find_element(By.CLASS_NAME, "next paginate_button").click()


# def handle_page_old(driver, atc, drug_f, sep):
#     res = []
#     # print(total_res)
#     elms = driver.find_elements(By.CLASS_NAME, "result")
#     res = collect_titles_dates(elms, atc, drug_f)
#     return res


def get_total_res(driver, sep):
    total_res = 0
    search_results_header = driver.find_element(By.ID, "search_results_header").text
    if "Your search returned no results. Showing results for" in search_results_header:
        print("TRIED TO CORRECT SPELLING")
        print(sep)
        return total_res, "SPELLING CORRECTION"
    elif "No results found" in search_results_header:
        print("NO SEARCH RESULTS FOUND")
        print(sep)
        return total_res, "NO SEARCH RESULTS"
    # print(search_results_header)
    if "Showing 1 result" in search_results_header:
        total_res = 1
    else:
        total_res = int(
            driver.find_element(By.CLASS_NAME, "total_results").text.split()[0]
        )
    return total_res, "SEARCH RESULT(S)"


def create_preview_urls(elm):
    preview_soup = BeautifulSoup(
        elm.find_element(By.CLASS_NAME, "preview_link").get_attribute("outerHTML"),
        "lxml",
    )
    href = preview_soup.find("a", href=True)["href"]
    product_url = "https://produktresume.dk" + href
    return product_url


def get_date(elm):
    elm_html = elm.get_attribute("outerHTML")  # gives exact HTML content of the element
    soup = BeautifulSoup(elm_html, "lxml")
    date_str = soup.find("span", class_="field_values").get_text().strip()
    date = datetime.strptime(date_str, "%d/%m/%Y")
    return date


def get_doc_title(soup):
    title = soup.find(id="document_title_link")["title"]
    return title


def get_elm_containing_text(soup, mytag, header_text, h):
    elm = soup.find(lambda tag: tag.name == mytag and header_text in tag.text)
    elm_text = h.handle(str(elm)).strip()
    if not elm_text.endswith(header_text):  # to check that
        print("elmText: ", repr(elm_text))
        raise Exception(
            "important text was likely included in {} element".format(header_text)
        )
    while elm.parent.name != "body":
        elm = elm.parent
    return elm


def get_category_text(soup, h, start_category, end_category):
    start_elm = get_elm_containing_text(soup, "span", start_category, h)
    end_elm = get_elm_containing_text(soup, "span", end_category, h)
    category_text = ""
    for elm in start_elm.find_next_siblings():
        if elm == end_elm:
            break
        else:
            if elm.name == "ol":
                if "list-style-type:none" in elm["style"]:
                    elm.name = "ul"
            new_text = h.handle(str(elm))
            # OBS!! What if for some reason these chars are in the middle of some text?
            new_text = new_text.replace("●", "").replace("\-", "")
            new_text = re.sub(r" +", " ", new_text)
            new_text = re.sub(r"\n+", "\n", new_text)
            category_text += new_text
    return category_text.strip()

    # html = ""
    # for elm in start_elm.find_next_siblings():
    #     if elm == end_elm:
    #         break
    #     else:

    #         html += str(elm)
    # return h.handle(html)


# def get_indications(soup, h):
#     start_elm = get_elm_containing_text(soup, "span", "Terapeutiske indikationer", h)
#     end_elm = get_elm_containing_text(soup, "span", "Dosering og administration", h)
#     indications = ""
#     for elm in start_elm.find_next_siblings():
#         # print(elm)
#         if elm == end_elm:
#             break
#         else:
#             # print("REPR")
#             # print(repr(h.handle(str(elm))))
#             indications += h.handle(str(elm))
#         # print("--")
#     return indications.strip()


def handle_page(driver, h):
    elms = driver.find_elements(By.CLASS_NAME, "result")
    dates_n_preview_urls = [(get_date(elm), create_preview_urls(elm)) for elm in elms]
    # print(*preview_urls, sep="\n")
    # dates = list(list(zip(*dates_n_preview_urls))[0])
    # print(dates)
    # dates.sort(reverse=True)
    # print(dates)
    for date, preview_url in dates_n_preview_urls[:2]:
        # print("date: ", date)
        # print("date: ", date.strftime("%d/%m/%Y"))
        driver.get(preview_url)
        driver.implicitly_wait(30)
        page_html = driver.page_source
        soup = BeautifulSoup(page_html, "lxml")
        title = get_doc_title(soup)
        print(title)
        # indications = get_category_text(
        #     soup, h, "Terapeutiske indikationer", "Dosering og administration"
        # )

        # print("INDICATIONS")
        # print(indications)

        contra_indications = get_category_text(
            soup,
            h,
            "Kontraindikationer",
            "Særlige advarsler og forsigtighedsregler vedrørende brugen",
        )
        print("\nCONTRAINDICATIONS")
        print(contra_indications)
        print("--------")


def make_search(driver, atc):
    h = html2text.HTML2Text()
    h.ignore_links = True
    h.single_line_break = True
    h.body_width = False
    h.re_ordered_list_matcher = False
    max_results_on_page = 10
    sep = "-------------------"
    res = {}
    url = get_search_url(atc)

    driver.get(url)
    driver.implicitly_wait(30)

    total_res, general_search_status = get_total_res(driver, sep)

    number_of_pages = total_res % max_results_on_page

    handle_page(driver, h)

    # if number_of_pages > 0:
    #     for i in range(1, number_of_pages):
    #         print("---------------NEW PAGE--------------------------")
    #         url = get_search_url(atc, i)
    #         driver.get(url)
    #         driver.implicitly_wait(30)
    #         handle_page(driver, h)

    # for i in range(number_of_pages - 1):
    #     pass
    # print(total_res, general_search_status)

    #     h = html2text.HTML2Text()
    #     h.ignore_links = True
    #     title = h.handle(str(title_div))


def get_titles_and_soups(driver, atc):
    # sep = "-------------------"
    # res = {}
    # url = get_search_url(atc)
    # print(url)
    # driver.get(url)
    # driver.implicitly_wait(30)
    res = make_search(driver, atc)
    return res


def main():
    overview = []
    # data = get_all_prioritized_data_with_or_without_indices()
    data = ["C09DA01"]
    driver = get_firefox_driver()

    try:
        for d in data:
            atc = d
            res_dict = get_titles_and_soups(driver, atc)
        print(res_dict)
    finally:
        driver.quit()

    # for o in overview:
    #     print(o)
    # driver.quit()
    # cols = ["ATC", "FORMULERING", "TOTAL_RES", "MATCH"]
    # for i in range(10):
    #     cols.append("TITLE")
    # write_to_csv(overview, cols, "docs_titles_found_by_atc_and_f")


if __name__ == "__main__":
    main()
