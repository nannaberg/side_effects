from get_drug_list_info import (
    get_all_data_with_indices,
    write_to_csv,
    write_to_csv_renal,
)
from bs4 import BeautifulSoup
import asyncio
import aiohttp
from time import perf_counter
import re

# import requests
import lxml.html as lh
import lxml.etree as etree
import lxml
import html2text
from html_sanitizer import Sanitizer
from collections import Counter
from flockhart.flockhart import get_flockhart_dict, get_drug_isoforms
import pandas as pd

pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)
pd.set_option("display.width", None)
pd.set_option("display.max_colwidth", None)

# global instances
H = html2text.HTML2Text()
H.ignore_links = True
H.bodywidth = 0

sanitizer = Sanitizer()


def sanitize_html_soup(html_soup):
    return sanitizer.sanitize(str(html_soup))


# Function to remove tags
def remove_tags(soup):

    for data in soup(["style", "script"]):
        # Remove tags
        data.decompose()

    # return data by retrieving the tag content
    return " ".join(soup.stripped_strings)


# # Print the extracted data
# print(remove_tags(page.content))


def get_dose_reduction_info(soup, atc, index):
    header = soup.find(lambda tag: tag.name == "h3" and "Doseringsforslag" in tag.text)
    dose_div = header.parent.find_next_sibling("div")

    pure_text = remove_tags(dose_div)
    if "skal nedsættes" in pure_text:
        print("{}, {}:\n {}\n".format(index, atc, pure_text))
    else:
        pass
        # print("{}, {}:\n NO INFO".format(index, atc))


# def get_liver_info(soup, atc, index):
#     header = soup.find(
#         lambda tag: tag.name == "h3" and "Nedsat leverfunktion" in tag.text
#     )
#     if header:
#         liver_div = header.parent.find_next_sibling("div")

#         pure_text = remove_tags(liver_div)
#         if "let" in pure_text:
#             print("{}, {}:\n {}\n".format(index, atc, pure_text))
#     else:
#         # pass
#         print("{}, {}, NO LIVER DOSE REDUCTION".format(index, atc))


def check_kidney_section_structure(kidney_div, atc, index):
    table = kidney_div.find("table")
    ul = kidney_div.find("ul")
    if table:
        # print("{}, {} HAS KIDNEY TABLE".format(index, atc))
        return "table"
    elif ul:
        # print("{}, {} HAS UL/LIST".format(index, atc))
        return "ul/list"
    else:
        # print("{}, {}".format(index, atc))
        gfr_sections = kidney_div.find_all("p", class_="glob-padTop20")

        calc_tag = kidney_div.find("div", class_="glob-padbtm20")
        # calc_tag = kidney_div.find_all("div", class_="glob-padbtm20")
        # if len(calc_tag) > 1:
        #     print("{}, {}: MORE THAN ONE glob-padbtm20 div".format(index, atc))

        if calc_tag:
            calc_siblings = calc_tag.findNextSiblings()
            # if calc_siblings:
            #     pass
            # print("{}, {}: MORE SIBLNGS".format(index, atc))
            for calc_sib in calc_siblings:
                if calc_sib.has_attr("class"):
                    if calc_sib["class"][0] != "referencer":
                        print("calc sib with class that is NOT referencer")
                        print(calc_sib.prettify())
                else:
                    print("{}, {}: MORE INFO".format(index, atc))
                    print(calc_sib.prettify())
                print("--------------------")

        else:
            pass
            # print("{}, {}: NO calc TAG".format(index, atc))
            # print("!!!there is more after calc!!!")
        # else:
        #     print("{}, {} NO calc TAG".format(index, atc))

        # print(calc_tag.text)
        # calc_ps = calc_tag


# def parse_nested_tables(html_content):
#     soup = BeautifulSoup(html_content, "html.parser")
#     main_table = soup.find("table")

#     df = pd.DataFrame(columns=["id", "col1", "col2", "col3"])

#     for row in main_table.find_all("tr"):
#         df_row = {}
#         df_row["id"] = row.get("id")

#         for i, cell in enumerate(row.find_all("td")):
#             if cell.find("table"):
#                 nested_table_html = str(cell.table)
#                 nested_df = pd.read_html(nested_table_html)[0]
#                 df_row[f"col{i+1}"] = nested_df
#             else:
#                 df_row[f"col{i+1}"] = cell.text.strip()

#         df = df.append(df_row, ignore_index=True)

#     return df


def get_renal_info(soup, atc, index):

    # res = []
    res = "na"
    no_tables = 0
    bool_inner_tables = False
    renal_header = soup.find(
        lambda tag: tag.name == "h3" and "Nedsat nyrefunktion" in tag.text
    )
    if renal_header:
        renal_div = renal_header.parent.find_next_sibling("div")
        tables = renal_div.select("div > table")
        rows = tables[0].find_all("tr")
        for row in rows:
            markdown = H.handle(sanitize_html_soup(row))
            print(markdown.strip())
            print("-------------")
        # print(index, atc, len(tables))
        # nested_tables = []
        # for table in tables:
        #     nested_tables.extend(table.find_all("table"))
        # if nested_tables:
        #     print("{}, {}, nested tables: {}".format(index, atc, len(nested_tables)))
        # for table in tables:
        #     print(table.prettify())
        #     print("\n\n")
        # table_1 = renal_div.find("div > table")
        # other_tables = table_1.find_next_siblings("table")
        # if table_1:
        #     print({index, atc, len(other_tables)})
        # else:
        #     print("{}, {}, NO TABLES".format(index, atc))
        # print(renal_div.prettify())
        # df = pd.read_html(str(renal_div))
        # print(df[0])
        # br()
        # print(df[1])
        # markdown_table = H.handle(str(renal_div))
        # print(markdown_table)
        # inner_tables = []

        # tables = renal_div.findAll("table")
        # no_tables = len(tables)

        # if no_tables == 2:
        #     for table in tables:
        #         if table.findAll("table"):
        #             bool_inner_tables = True
        # if not tables:
        #     print("{}, {}: RENAL BUT NO TABLE".format(index, atc))
        # for table in tables:
        #     all_inner_tables = table.findAll("table")
        #     if all_inner_tables:
        #         bool_inner_tables = True
        #         inner_tables.append(len(all_inner_tables))
        #     else:
        #         inner_tables.append(0)
        # # print("{}, {}: table length: {}".format(index, atc, len(tables)))
        # res = inner_tables
        # h = html2text.HTML2Text()
        # h.ignore_links = True
        # res = H.handle(str(renal_div))

    return (no_tables, bool_inner_tables, res)


def get_header(soup, text_header):
    return soup.find(lambda tag: tag.name == "h3" and text_header in tag.text)


def get_text(soup, atc_code, index, text_header):
    # header = soup.find(lambda tag: tag.name == "h3" and text_header in tag.text)
    header = get_header(soup, text_header)

    res = "na"
    if header:

        if not header.text.strip() == text_header:
            raise Exception(
                "Ambiguity regarding {text_header} header: {atc_code}, {index}"
            )

        div = header.parent.find_next_sibling("div")
        # h = html2text.HTML2Text()
        # h.ignore_links = True
        res = H.handle(sanitize_html_soup(div))
        # res = H.handle(str(div))
    return res


def get_liver_info(soup, atc_code, index, text_header):

    header = soup.find(lambda tag: tag.name == "h3" and text_header in tag.text)

    res = "Nej"
    if header:
        if not header.text.strip() == text_header:
            raise Exception(
                "Ambiguity regarding {} header: {}, {}".format(
                    text_header, atc_code, index
                )
            )

        div = header.parent.find_next_sibling("div")
        # h = html2text.HTML2Text()
        # h.ignore_links = True
        res = H.handle(sanitize_html_soup(div))
        # print(res)
        # res = H.handle(str(div))
    return res


# problem: sometimes several halftimes are indicated
def get_halftime(soup, atc, index, text_header):
    res = "na"
    farmakokinetik = get_text(soup, atc, index, text_header)
    lines = farmakokinetik.split("\n")
    halftime_lines = []
    for line in lines:
        if "halveringstid" in line:
            halftime_lines.append(line)

    if halftime_lines:
        res = "\n".join(halftime_lines)
        # if len(halftime_lines) > 1:
        #     print("MORE THAN TWO LINES, halftimes for {}, {}".format(atc, index))
        #     print(farmakokinetik)
        #     print("---------------\n")
    # else:
    #     print("NO LINES for {}, {}".format(atc, index))
    #     print(farmakokinetik)
    #     print("--------------------\n")
    return res


def br():
    print("\n")


def get_revision_date(soup, atc, index):
    text_header = "Revisionsdato"
    header = get_header(soup, text_header)
    markdown_text = H.handle(str(header.parent))
    pattern = r"\d{2}\.\d{2}\.\d{4}"
    res = re.findall(pattern, markdown_text)
    if len(res) == 0:
        print("NO DATES: ", atc, index)
    if len(res) > 1:
        print("MORE THAN ONE DATE: ", atc, index)
    return res[0]


def get_pharmaceutical_form(soup, atc, index):
    text_header = "Dispenseringsform"
    markdown_text = get_text(soup, atc, index, text_header)
    pattern = r"\*{2}(.*?)\*{2}"
    res = re.findall(pattern, markdown_text)
    return res


def get_pharma_html(soup, atc, index):
    text_header = "Dispenseringsform"
    # markdown_text = get_text(soup, atc, index, text_header)
    # pattern = r"\*{2}(.*?)\*{2}"
    # res = re.findall(pattern, markdown_text)
    # return res

    # first task: just figure out if any of the known pharmaforms can be found in the non-strong text segments

    header = get_header(soup, text_header)
    if header:

        if not header.text.strip() == text_header:
            raise Exception(
                "Ambiguity regarding {text_header} header: {atc_code}, {index}"
            )

        div = header.parent.find_next_sibling("div")

    # all_ps = div.find_all("p")
    # res = [p.text for p in all_ps]
    # all_b_tags = div.find_all("b")
    # if not all_b_tags:
    #     print("{}, {}:".format(index, atc))
    # print(*res, sep="\n--- ")
    # print("--------------------------")

    return div

    # all_li_tags = div.find_all("li")
    # if all_li_tags:
    #     print("{}, {}:".format(index, atc))
    #     # print(len(all_sibling_b_tags))
    #     print(*res, sep="\n--- ")
    #     print("--------------------------")

    # all_sibling_b_tags = []

    # for b_tag in all_bs:
    #     sibling_b_tags = []
    #     for sibling in b_tag.find_all_next("b"):
    #         all_sibling_b_tags.append(sibling)
    #     # all_sibling_b_tags.append(sibling_b_tags)
    # if all_sibling_b_tags:
    #     print("{}, {}:".format(index, atc))
    #     print(len(all_sibling_b_tags))
    #     print(*res, sep="\n--- ")
    #     print("--------------------------")
    # if len(all_bs) < 1:
    #     print("{}, {}: NO B's!!!".format(index, atc))

    # if len(all_ps) != len(all_bs):
    #     only_dot = soup.find_all(lambda tag: tag.name == "b" and tag.text == ".")
    #     print("{}, {}:".format(index, atc))
    #     print(*res, sep="\n--- ")
    #     if only_dot:
    #         print("<b> with ONLY DOT")
    #     print("--------------------------")

    # return res


def get_active_substances(soup, atc, index):
    active_substances = []
    parent = soup.find(attrs={"class": "SpaceBtm IndholdsstofferHeaderLinks"})
    if parent == None:
        noparent = soup.find(
            title="Lægemidlet kan være helt udgået eller midlertidigt udgået pga. leveringssvigt"
        )
        print("In get_generic_name: Parent was none, index: ", index)
        # print(noparent.text)
        # return noparent.text
        return active_substances
    children = parent.find_all("b")

    for b in children:
        active_substances.append(b.text)
    return active_substances


def get_cyp(soup, atc, index, flockhart_dict):
    active_substances = get_active_substances(soup, atc, index)
    res = {}
    if active_substances:
        # if len(active_substances) > 1:
        #     return "more than 1 active substance"
        # else:
        active_substance = active_substances[0].lower()
        isoform_dict = get_drug_isoforms(active_substance, flockhart_dict)
        # print(
        #     "{0}, {1}, {2:<40} {3}".format(index, atc, active_substance, isoform_dict)
        # )

        more_substances = len(active_substances) > 1

        for key, value in isoform_dict.items():
            new_key = "CYP-" + key.lower()[:-1]
            # print(new_key)
            if value:
                if more_substances:
                    res[new_key] = "More than one active substance"
                else:
                    res[new_key] = ",".join(value)
            else:
                if more_substances:
                    res[new_key] = "More than one active substance"
                else:
                    res[new_key] = "No"
    else:  # to accommodate for no active substances found, quite hacky
        for key in flockhart_dict.keys():
            new_key = "CYP-" + key.lower()[:-1]
            res[new_key] = ["no active substances"]
    return res


async def get(
    session: aiohttp.ClientSession,
    data: list,
    flockhart_dict: dict,
):
    l_active_substance = data[1].lower()
    m_active_substance = data[2]
    # l_pharma_form = data[1]
    l_atc = data[3]
    l_name = data[4]
    index = data[5]
    url = "https://pro.medicin.dk/Medicin/Praeparater/{}".format(index)

    # h = html2text.HTML2Text()
    # h.ignore_links = True
    # h.bodywidth = 0
    # if int(index) != 2525:
    # if int(index) != 7837:
    #     return None
    # testresp = requests.get(url)
    # testtext = testresp.text
    # print(testtext)

    try:
        async with session.get(url) as response:

            status = response.status
            length = response.content_length
            if status == 200 and length > 9000:
                page = await response.text()
                soup = BeautifulSoup(page, "lxml")
                basis = {}
                basis["Index"] = index
                basis["Atc"] = l_atc
                basis["Pharmaceutical form"] = get_pharmaceutical_form(
                    soup, l_atc, index
                )
                # basis = [index, l_atc]
                basis["Revision date"] = get_revision_date(soup, l_atc, index)
                text_header_dict = {
                    "Anvendelsesområder": "Registered indication",
                    "Kontraindikationer": "Contraindications",
                    "Forsigtighedsregler": "Warnings and precautions",
                }
                # text_headers = [
                #     "Anvendelsesområder",
                #     "Kontraindikationer",
                #     "Forsigtighedsregler",
                # ]
                for text_header_danish, text_header_english in text_header_dict.items():
                    basis[text_header_english] = get_text(
                        soup, l_atc, index, text_header_danish
                    )
                    # if text_header == "Forsigtighedsregler":
                    #     print(get_text(soup, l_atc, index, text_header))
                basis["Dosereduction liver"] = get_liver_info(
                    soup, l_atc, index, "Nedsat leverfunktion"
                )

                # basis["Pharmaceutical form"] = get_pharmaceutical_form(
                #     soup, l_atc, index
                # )

                cyp_dict = get_cyp(soup, l_atc, index, flockhart_dict)
                for k, v in cyp_dict.items():
                    basis[k] = v
                basis["Halftime"] = get_halftime(soup, l_atc, index, "Farmakokinetik")

                basis["Pharma html"] = get_pharma_html(soup, l_atc, index)

                # basis.append(get_halftime(soup, l_atc, index, "Farmakokinetik"))
                # basis.append(get_registered_indications(soup, l_atc, index))
                # get_liver_info(soup, l_atc, index)
                # basis.append(get_contraindications(soup, l_atc, index))
                # basis["eGFR"] = get_renal_info(soup, l_atc, index)

                return basis
                # get_dose_reduction_info(soup, l_atc, index)

            else:
                print("{}, not success or not long enough".format(index))
    except asyncio.TimeoutError:
        print("timeout error on index: ", index)


def without_keys(d, keys):
    return {x: d[x] for x in d if x not in keys}


def handle_scraping_results(input):
    # print("SCRAPING RES")
    # print(*res, sep="\n\n")
    final_res = []
    pharma_key = "Pharmaceutical form"
    # atc_codes = list(set([x["Atc"] for x in final_res]))
    for d in input:
        pharma_forms = d[pharma_key]
        # print(d["Index"], d["Atc"], len(pharma_forms))
        for p in pharma_forms:
            new_dict = {}
            for k, v in d.items():
                if k != pharma_key:
                    new_dict[k] = v
                else:
                    new_dict[k] = p
            final_res.append(new_dict)
    # print("FINAL RES")
    # print(*final_res, sep="\n\n")
    return final_res


def remove_pharma_duplicates(input):
    # removes duplicate entries in list regarding atc and pharmaceutical form, keep the one with the latest date, otherwise the first encountered
    # seen has (atc, pharmaceutical form, date)

    atc_key = "Atc"
    pharma_key = "Pharmaceutical form"
    date_key = "Revision date"
    df = pd.DataFrame.from_dict(input)
    cols_to_print = ["Index", atc_key, pharma_key, date_key]
    # print(df[cols_to_print])
    df = df.sort_values(date_key).drop_duplicates([atc_key, pharma_key], keep="last")
    df = df.sort_values([atc_key, "Index"], ascending=[True, True])
    # print(df[cols_to_print])
    return df


async def main(data):
    timeout = aiohttp.ClientTimeout(total=6 * 60)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        flockhart_dict = get_flockhart_dict()
        scraping_res = await asyncio.gather(
            *[get(session, d, flockhart_dict) for d in data]
        )
        only_res = [r for r in scraping_res if r]
        pharma_expanded_res = handle_scraping_results(only_res)
        pharma_duplicate_free_df = remove_pharma_duplicates(pharma_expanded_res)
        dst = "working_example.csv"
        pharma_duplicate_free_df.to_csv(dst, index=False)

        # columns = final_res[0].keys()
        # write_to_csv_renal(
        #     final_res,
        #     columns,
        #     "working_example",
        # )


if __name__ == "__main__":
    data = get_all_data_with_indices()
    # print(len(data))
    # print(*data[:10], sep="\n")

    start = perf_counter()
    # print(data[0])
    indices = ["4104", "5988", "5965", "9989"]
    indices = ["3380"]
    indices = ["10675"]
    indices = ["5988", "5965", "10675"]
    # indices = ["2605", "8316", "9517"]
    # data_used = [d for d in data if d[5] in indices[0]]
    # print(data_used)
    data_used = data
    # data_used = [d for d in data if d[4] == "5965"]
    # print(data_used)
    asyncio.run(main(data_used))
    end = perf_counter()

    # print(f"{len(data) / (end - start)} req/s")
    # print("total time: ", end - start)
