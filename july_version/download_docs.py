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
href = ""


def get_search_url(drug):
    base_url = "https://produktresume.dk/AppBuilder/search?utf8=%E2%9C%93&q="
    end_base_url = "&button=search"
    # print(drug)
    parts = drug.split()
    url = base_url + parts[0]
    for part in parts[1:]:
        url += "+" + part
    url += end_base_url
    return url


# def get_search_page(url):
#     response = requests.get(url)


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


def download_file(driver, drug_name):
    url = get_search_url(drug_name)
    driver.get(url)
    driver.implicitly_wait(30)
    driver.find_element(By.CLASS_NAME, "before_preview_link").click()
    driver.quit()


def explore_search_results(driver, drug_name, drug_f):
    titles = []
    url = get_search_url(drug_name)
    # print(url)
    driver.get(url)
    driver.implicitly_wait(30)
    elms = driver.find_elements(By.CLASS_NAME, "result")
    # print(len(elms))
    found = 0
    for elm in elms:
        elm_html = elm.get_attribute(
            "outerHTML"
        )  # gives exact HTML content of the element
        soup = BeautifulSoup(elm_html, "lxml")
        # print(soup.a.prettify())
        title = soup.a.get_text()
        # print("Whole title: ", title)
        if not "," in title:
            print(
                "\t{}, {} -- TITLE: {} HAS NO COMMA, SO IT IS IGNORED: ".format(
                    drug_name, drug_f, title
                )
            )
            continue
        parts = title.split(",", 1)
        # print("len parts: ", len(parts))
        # print("drug name document: ", parts[0])
        # print("drug_f doc: ", parts[1])
        if drug_name in parts[0] and all(f in parts[1] for f in drug_f.split(",")):
            found += 1
            # print("{}: ok".format(title))
        # print("----------\n")
        titles.append(title)
        # text = print(soup.get_text())
        # print(text)
    if len(elms) < 1:
        print("\t{}, {} -- NO SEARCH RESULTS ".format(drug_name, drug_f))
    elif found == 0:
        print("\t{}, {} -- NOT FOUND ".format(drug_name, drug_f))
        # print("----------\n")
    elif found > 1:
        print("\t{}, {} -- FOUND {} MATCHES".format(drug_name, drug_f, found))
        # print("----------\n")
    else:
        print("{}, {}".format(drug_name, drug_f))
    return titles


def main():

    download_data = get_all_docs_titles()
    # 0,1,2
    # rest is titles
    no_search_results = []
    not_found = []
    only_name_found = []
    more_than_one_found = []
    for d in download_data:
        found = 0
        partially_found = 0
        drug_name = d[1]

        drug_f = d[2]
        titles = [t for t in d[3:] if t]
        found_titles = []

        for title in d[3:]:
            parts = title.split(",", 1)
            if drug_name in parts[0]:
                if all(f in parts[1] for f in drug_f.split(",")):
                    found += 1
                    found_titles.append(title)
                else:
                    partially_found += 1

        to_append = [drug_name, drug_f, found_titles]
        if len(titles) < 1:
            no_search_results.append(to_append)
        if found == 0 and partially_found == 0:
            not_found.append(to_append)
        if found == 0 and partially_found > 0:
            only_name_found.append(to_append)
        elif found > 1:
            more_than_one_found.append(to_append)

    for line in more_than_one_found:
        print(line[:2])
        for t in line[2]:
            print("\t\t", t)

    # print("NO SEARCH RESULTS:")
    # for line in no_search_results:
    #     print(line[:2])
    # print("------------------")
    # print("NOT FOUND:")
    # for line in not_found:
    #     print(line[:2])
    # print("----------------------")
    # print("ONLY NAME FOUND:")
    # for line in only_name_found:
    #     print(line[:2])
    # print("----------------------")
    # print("MORE THAN ONE FOUND:")
    # for line in more_than_one_found:
    #     print(line[:2])
    # print("----------------------")
    # print("Number of no search results: ", len(no_search_results))
    # print("Number of not found: ", len(not_found))
    # print("Number of only name found: ", len(only_name_found))
    # print("Number of more_than_one_found: ", len(more_than_one_found))
    # print("---------------------")

    # tofix:
    # - correct to lowercase to avoid a few cases
    # - check for each if search results have not been found on the webpage and run the whole thing again.
    # - problemer med formuleringer indeholdt i andre formuleringer:
    #   - kapsler, depotkapsler
    #   - tabletter, enterotabletter, smeltetabletter
    #   - oramorph, oral opløsning, oralopløsning enkeltdosisbeholdere
    # overview = []
    # data = get_all_prioritized_data_with_or_without_indices()
    # driver = get_firefox_driver()
    # for i, d in enumerate(data):
    #     drug_f = d[1]
    #     drug_name = d[3].replace('"', "")
    #     titles = explore_search_results(driver, drug_name, drug_f)
    #     temp = [drug_name, drug_f]
    #     temp.extend(titles)
    #     overview.append(temp)

    # driver.quit()
    # cols = ["DRUG_NAME", "FORMULERING"]
    # for i in range(10):
    #     cols.append("TITLE")
    # write_to_csv(overview, cols, "docs_titles_found")


if __name__ == "__main__":
    main()


# Amlodipin+%22Taw+Pharma%22&button=search

# response = requests.get(url)
# file_Path = "research_Paper_1.pdf"

# if response.status_code == 200:
#     with open(file_Path, "wb") as file:
#         file.write(response.content)
#     print("File downloaded successfully")
# else:
#     print("Failed to download file")
