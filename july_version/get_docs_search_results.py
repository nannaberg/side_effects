import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
import os.path
from drug_list_handling import (
    get_all_prioritized_data_with_or_without_indices,
    write_to_csv,
    get_all_docs_titles,
)
import pandas as pd

doc_base_url = "https://produktresume.dk"


def get_search_url(atc):
    base_url = "https://produktresume.dk/AppBuilder/search?utf8=%E2%9C%93&q="
    end_base_url = "&button=search"
    # A11HA08, N05BA
    # "C+01+BD+01+" + OR + "C01BD01"
    indices = [0, 1, 3, 5]
    parts = [
        atc[i:j] for i, j in zip(indices, indices[1:] + [None]) if atc[i:j]
    ]  # for splitting up atc: A11HA08 -> A 11 HA 08 (might be how it is written in document)
    # if atc == "N05BA":
    #     print(parts)
    url = base_url + '"'
    for p in parts:
        url += p + "+"
    url += '"+OR+"' + atc + '"'
    url += end_base_url

    # url = base_url + "blabla" + end_base_url
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

    # apparently necessary because it is snap firefox
    service = Service(executable_path="/snap/bin/geckodriver")

    return webdriver.Firefox(options=options, service=service)


def explore_search_results(driver, atc, drug_f):
    sep = "-------------------"
    titles = []
    match = ""
    total_res = 0
    url = get_search_url(atc)
    # print(url)
    driver.get(url)
    driver.implicitly_wait(30)
    search_results_header = driver.find_element(By.ID, "search_results_header").text
    if "Your search returned no results. Showing results for" in search_results_header:
        print("TRIED TO CORRECT SPELLING")
        print(sep)
        return titles, -2, match
    elif "No results found" in search_results_header:
        print("NO SEARCH RESULTS FOUND")
        print(sep)
        return titles, -1, match
    # print(search_results_header)
    if "Showing 1 result" in search_results_header:
        total_res = 1
    else:
        total_res = driver.find_element(By.CLASS_NAME, "total_results").text.split()[0]
    # print(total_res)
    elms = driver.find_elements(By.CLASS_NAME, "result")
    # print("len(elms): ", len(elms))
    found = 0
    for elm in elms:
        elm_html = elm.get_attribute(
            "outerHTML"
        )  # gives exact HTML content of the element
        soup = BeautifulSoup(elm_html, "lxml")
        # print(soup.a.prettify())
        title = soup.a.get_text()
        date = soup.find("span", class_="field_values").get_text().strip()
        # print("Whole title: ", title)
        if not "," in title:
            print(
                "\t{}, {} -- TITLE: {} HAS NO COMMA, SO IT IS IGNORED: ".format(
                    atc, drug_f, title
                )
            )
            continue
        web_f = title.split(",", 1)[1]
        if all(f in web_f for f in drug_f.split(",")):
            found += 1
        titles.append(date + "," + title)
        # print(text)
    if len(elms) < 1:
        print("\t{}, {} -- NONO SEARCH RESULTS ".format(atc, drug_f))
    elif found == 0:
        print("\t{}, {} -- NOT FOUND ".format(atc, drug_f))
        match = found
        # print("----------\n")
    elif found > 1:
        print("\t{}, {} -- FOUND {} MATCHES".format(atc, drug_f, found))
        match = found
        # print("----------\n")
    else:
        print("{}, {} -- FOUND EXACTLY ONE MATCH".format(atc, drug_f))
        match = found
    print(sep)
    return titles, total_res, match


def main():
    overview = []
    data = get_all_prioritized_data_with_or_without_indices()
    driver = get_firefox_driver()
    for d in data:
        drug_f = d[1]
        atc = d[2]
        titles, total_res, match = explore_search_results(driver, atc, drug_f)
        temp = [atc, drug_f]
        temp.append(total_res)
        temp.append(match)
        temp.extend(titles)
        overview.append(temp)

    # for o in overview:
    #     print(o)
    driver.quit()
    cols = ["ATC", "FORMULERING", "TOTAL_RES", "MATCH"]
    for i in range(10):
        cols.append("TITLE")
    write_to_csv(overview, cols, "docs_titles_found_by_atc_and_f")


if __name__ == "__main__":
    main()
