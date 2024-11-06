from get_drug_list_info import (
    get_all_data_with_indices,
    get_data_not_on_promed,
    write_to_csv,
    write_to_csv_renal,
)
from bs4 import BeautifulSoup
import asyncio
import aiohttp
from time import perf_counter
import re
from io import StringIO

# import requests
import lxml.html as lh
import lxml.etree as etree
import lxml
import html2text
from html_sanitizer import Sanitizer
from collections import Counter
import pandas as pd
from datetime import datetime

pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)
pd.set_option("display.width", None)
pd.set_option("display.max_colwidth", None)

# global instances
H = html2text.HTML2Text()
H.ignore_links = True
H.body_width = 0

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


def get_sanitized_html_markdown_text(soup):
    sanitized_html = sanitizer.sanitize(str(soup))

    markdown_text = H.handle(sanitized_html)
    return markdown_text


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
        all_tables = renal_div.find_all("table")
        # print(len(all_tables))
        # outer_tables = []
        first_table = renal_div.find("table")
        if first_table:
            outer_tables = [first_table] + first_table.find_next_siblings("table")
            # print(len(outer_tables))
            # print(index, atc, len(all_tables), len(outer_tables))
            if len(outer_tables) != len(all_tables):
                res = "Nested table - to be done manually"
            else:
                res = ""
                for table in outer_tables:
                    df = pd.read_html(StringIO(str(table)))
                    if len(df) != 1:
                        raise Exception(
                            "Discrepancy regarding number of renal tables: {atc_code}, {index}"
                        )
                    text_version = df[0].to_string(index=False)
                    res += text_version + "\n"
        else:
            res = get_sanitized_html_markdown_text(renal_div)
        # res = renal_div

    return res


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
        res = H.handle(sanitize_html_soup(div))
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
        res = H.handle(sanitize_html_soup(div))
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
    date = datetime.strptime(res[0], "%d.%m.%Y")
    # print(res[0], date)
    return date


def remove_annoying_commas(index, atc, markdown_text):
    annoying_commas = ["** ,**", "** , **"]
    altered_markdown = markdown_text
    for comma in annoying_commas:
        if comma in markdown_text:
            altered_markdown = altered_markdown.replace(comma, ",")
            print("ANNOYING COMMA WAS HERE: ", index, atc)
    return altered_markdown


def remove_annoying_punctuation_from_non_bold(index, atc, non_bold):
    annoying_periods = [
        "_**.**_",
        "**.**",
        "_._",
    ]
    match = False
    res = []
    for nb in non_bold:
        new_nb = nb
        for period in annoying_periods:
            if period in new_nb:
                new_nb = new_nb.replace(period, ".")
                match = True
                # print("ANNOYING PERIOD: ", atc, index)
                # print("nb: \n", nb)
                # print("new nb: \n", new_nb)
                # print("--------------")
        if new_nb[0] == ".":
            match = True
            # print(new_nb)
            new_nb = new_nb[1:].strip()
            # print(new_nb)
        if new_nb[-1] == "*" and new_nb[-2:] != "**":
            match = True
            new_nb = new_nb[:-1].strip()
        res.append(new_nb)
        # if match:
        # print(nb)
        # print(new_nb)
        # print("---------------")
    return res


def remove_last_period(pharma_forms):
    res = [f[:-1] if f[-1] == "." else f for f in pharma_forms]
    res = [r for r in res if r]
    return res


def get_all_bold(atc, index, markdown_text, pattern, exclusion_list):
    res = re.findall(pattern, markdown_text)
    res = [r for r in res if r not in exclusion_list]
    contains_colored_tablets = False
    for r in res:
        if "tabletter" in r:
            # to check for the 21 lyserøde tabletter, 21 tabletter cases
            if r[0].isdigit():
                contains_colored_tablets = True
                break
    if contains_colored_tablets:
        res = ["Tabletter"]
    #     print("{}, {}".format(index, atc))
    #     print(res)
    #     print("-----------------------")
    return res, contains_colored_tablets


def make_bold_weird(sub):
    res = "~".join(sub[2:-2])
    res = "~" + res + "~"
    return res


def make_weird_bold(sub):
    res = sub.replace("~", "")
    res = "**" + res + "**"


def get_all_non_bold(
    atc, index, markdown_text, pattern, exclusion_list, contains_colored_tablets
):
    # for cases like 21 lyserøde tabletter, 7 hvide tabletter
    if contains_colored_tablets:
        res = [markdown_text]
    else:
        # goal: split the markdown by the pharma forms without including the pharma forms, and also avoid splitting by any of the bold forms of the exclusion list. The number of pharma forms and non-bold sections should match each other.
        bold_exclusion_list = ["**" + x + "**" for x in exclusion_list]
        weird_exclusion_list = [make_bold_weird(b) for b in bold_exclusion_list]
        altered_markdown = markdown_text
        # avoiding splitting by members of exclusion list by replacing them with "weird" versions (eg **Obs.** becomes ~O~b~s~.~) to easily find and return them to original **Obs** after the split.
        for i in range(len(bold_exclusion_list)):
            altered_markdown = altered_markdown.replace(
                bold_exclusion_list[i], weird_exclusion_list[i]
            )
        split_text = [
            part.strip()
            for part in re.split(pattern, altered_markdown)
            if part and not re.match(pattern, "**" + part + "**")
        ]
        # have to use this trick with ||| join to keep the non-bold in list form instead of one big string
        joined_split_text = "|||".join(split_text)
        for i in range(len(weird_exclusion_list)):
            joined_split_text = joined_split_text.replace(
                weird_exclusion_list[i], bold_exclusion_list[i]
            )
        res = joined_split_text.split("|||")

    return res


def get_pharmaceutical_form(soup, atc, index):
    text_header = "Dispenseringsform"
    markdown_text = get_text(soup, atc, index, text_header)
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
    markdown_text = remove_annoying_commas(index, atc, markdown_text)
    pharma_forms, contains_colored_tablets = get_all_bold(
        atc, index, markdown_text, pattern, exclusion_list
    )
    pharma_forms = remove_last_period(pharma_forms)
    pharma_non_bold = get_all_non_bold(
        atc, index, markdown_text, pattern, exclusion_list, contains_colored_tablets
    )

    new_pharma_forms = []
    if len(pharma_forms) != len(pharma_non_bold):
        print(
            "--------bold and nonbold dont fit: {}, {}--------------".format(index, atc)
        )
        print(index, atc, pharma_forms)
        print(pharma_non_bold)
        # print(markdown_text)
        # # print(*pharma_forms, sep="\n-")
        # print("-----------------------------")
    else:
        for bold, non_bold in zip(pharma_forms, pharma_non_bold):
            if "filmovertruk" in non_bold:
                # print("{}, {}, {}: {}".format(index, atc, bold, non_bold))
                new_pharma_forms.append(bold + ", filmovertrukne")
            elif "sukkerovertruk" in non_bold:
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
    pharma_non_bold = remove_annoying_punctuation_from_non_bold(
        index, atc, pharma_non_bold
    )
    pharma_forms = new_pharma_forms
    return pharma_forms, pharma_non_bold


def get_pharma_html(soup, atc, index):
    text_header = "Dispenseringsform"
    header = get_header(soup, text_header)
    if header:

        if not header.text.strip() == text_header:
            raise Exception(
                "Ambiguity regarding {text_header} header: {atc_code}, {index}"
            )

        div = header.parent.find_next_sibling("div")

    return div


async def get(
    session: aiohttp.ClientSession,
    data: list,
):
    l_active_substance = data[1].lower()
    m_active_substance = data[2]
    # l_pharma_form = data[1]
    l_atc = data[3]
    l_name = data[4]
    index = data[5]
    url = "https://pro.medicin.dk/Medicin/Praeparater/{}".format(index)

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
                basis["Active substance"] = data[1]
                basis["Atc"] = l_atc
                # if index == "na":

                basis["Pharmaceutical form"], basis["Pharmaceutical form dosage"] = (
                    get_pharmaceutical_form(soup, l_atc, index)
                )
                # basis = [index, l_atc]
                basis["Revision date"] = get_revision_date(soup, l_atc, index)
                text_header_dict = {
                    "Doseringsforslag": "Dosage",
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

                basis["Halftime"] = get_halftime(soup, l_atc, index, "Farmakokinetik")

                # basis["Pharma html"] = get_pharma_html(soup, l_atc, index)

                # basis.append(get_halftime(soup, l_atc, index, "Farmakokinetik"))
                # basis.append(get_registered_indications(soup, l_atc, index))
                # get_liver_info(soup, l_atc, index)
                # basis.append(get_contraindications(soup, l_atc, index))
                basis["eGFR"] = get_renal_info(soup, l_atc, index)

                return basis

            else:
                print("{}, not success or not long enough".format(index))
    except asyncio.TimeoutError:
        print("timeout error on index: ", index)


def without_keys(d, keys):
    return {x: d[x] for x in d if x not in keys}


def expand_pharma_forms_scraping_results(input):
    # print("SCRAPING RES")
    # print(*res, sep="\n\n")
    final_res = []
    forms_key = "Pharmaceutical form"
    amount_key = "Pharmaceutical form dosage"
    return df.explode([forms_key, amount_key], ignore_index=True)
    # atc_codes = list(set([x["Atc"] for x in final_res]))
    for d in input:
        pharma_forms = d[forms_key]
        pharma_amount = d[amount_key]
        # print(d["Index"], d["Atc"], len(pharma_forms))
        for form, amount in zip(pharma_forms, pharma_amount):
            new_dict = {}
            for k, v in d.items():

                if k != forms_key:
                    new_dict[k] = v
                else:
                    new_dict[k] = form
            final_res.append(new_dict)
    # print("FINAL RES")
    # print(*final_res, sep="\n\n")
    return final_res


def expand_pharma_forms(input):
    forms_key = "Pharmaceutical form"
    amount_key = "Pharmaceutical form dosage"
    df = pd.DataFrame.from_dict(input)
    df = df.explode([forms_key, amount_key], ignore_index=True)
    return df


def remove_pharma_duplicates(pharma_expanded_df):
    # removes duplicate entries in list regarding atc and pharmaceutical form, keep the one with the latest date, otherwise the first encountered
    # seen has (atc, pharmaceutical form, date)

    atc_key = "Atc"
    pharma_key = "Pharmaceutical form"
    date_key = "Revision date"
    # df = pd.DataFrame.from_dict(input)
    df = pharma_expanded_df
    cols_to_print = ["Index", atc_key, pharma_key, date_key]
    # print(df[cols_to_print])
    df = df.sort_values(date_key).drop_duplicates([atc_key, pharma_key], keep="last")
    df = df.sort_values([atc_key, "Index"], ascending=[True, True])
    # print(df[cols_to_print])
    return df


async def main(data, data_not_on_promed):
    timeout = aiohttp.ClientTimeout(total=6 * 60)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        scraping_res = await asyncio.gather(*[get(session, d) for d in data])
        only_res = [r for r in scraping_res if r]

        # print(*only_res, sep="\n")
        print("original res: ", len(only_res))
        pharma_expanded_df = expand_pharma_forms(only_res)
        cols_to_print = [
            "Index",
            "Atc",
            "Pharmaceutical form",
            "Pharmaceutical form dosage",
            "Revision date",
        ]
        # print(pharma_expanded_df[cols_to_print])
        print("expanded res: ", pharma_expanded_df.shape[0])
        pharma_duplicate_free_df = remove_pharma_duplicates(pharma_expanded_df)
        print("duplicate free res: ", pharma_duplicate_free_df.shape[0])
        # print(pharma_duplicate_free_df[cols_to_print])
        dst = "working_example.csv"
        # cols = pharma_duplicate_free_df.columns
        # cols.remove("Pharmaceutical form dosage")
        # print(cols)
        # print(type(cols))
        final_pharma_df = pharma_duplicate_free_df.loc[
            :, pharma_duplicate_free_df.columns != "Pharmaceutical form dosage"
        ]
        print(final_pharma_df.columns)
        for d in data_not_on_promed:
            new_row = {"Index": "na", "Active substance": d[0], "Atc": d[1]}
            start_index = len(new_row)
            for col in final_pharma_df.columns[start_index:]:
                new_row[col] = "na"
            # print(new_row)
            final_pharma_df = final_pharma_df._append(new_row, ignore_index=True)

        # print(final_pharma_df[-3:])
        final_pharma_df = final_pharma_df.sort_values(
            ["Atc", "Index"], ascending=[True, True]
        )
        final_pharma_df.to_csv(dst, index=False)

        # columns = final_res[0].keys()
        # write_to_csv_renal(
        #     final_res,
        #     columns,
        #     "working_example",
        # )


if __name__ == "__main__":
    data = get_all_data_with_indices()
    data_not_on_promed = get_data_not_on_promed()
    print("DAAT NOT ON PROMED: ", data_not_on_promed)
    # print(len(data))
    # print(*data[:10], sep="\n")

    to_skip = ["A01AB09", "A06AD15", "M02AA07", "A10AC04", "A10AE54", "A10BD10"]
    to_keep_empty = ["A06AG02", "N02CX02"]

    start = perf_counter()
    # print(data[0])
    indices = ["4104", "5988", "5965", "9989"]
    indices = ["3380"]
    indices = ["10675"]
    indices = ["5988", "5965", "10675"]
    # indices = ["2605", "8316", "9517"]
    # data_used = [d for d in data if d[5] in indices[0]]
    # print(data_used)
    data_used = data[:50]
    # data_used = [d for d in data if d[4] == "5965"]
    # print(data_used)
    asyncio.run(main(data_used, data_not_on_promed))
    end = perf_counter()

    # print(f"{len(data) / (end - start)} req/s")
    # print("total time: ", end - start)