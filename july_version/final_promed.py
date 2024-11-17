from bs4 import BeautifulSoup
import asyncio
import aiohttp
from time import perf_counter
import re
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
H.single_line_break = True

sanitizer = Sanitizer()


def get_all_data_with_indices():
    df = pd.read_csv("final_drugs_with_indices.csv", keep_default_na=False)
    values = df.values.tolist()
    return [x for x in values if x[5] != "na"]


def get_data_not_on_promed():
    df = pd.read_csv("final_drugs_with_indices.csv", keep_default_na=False)
    values = df.values.tolist()
    to_skip = ["A01AB09", "A06AD15", "M02AA07", "A10AC04", "A10AE54", "A10BD10"]
    return [[x[1], x[3]] for x in values if x[3] not in to_skip and x[5] == "na"]


def get_sanitized_html_markdown_text(soup):
    sanitized_html = sanitizer.sanitize(str(soup))

    markdown_text = H.handle(sanitized_html)
    return markdown_text


def get_header(soup, text_header):
    return soup.find(lambda tag: tag.name == "h3" and text_header in tag.text)


def get_text(soup, atc_code, index, text_header):
    header = get_header(soup, text_header)

    res = "na"
    if header:

        if not header.text.strip() == text_header:
            raise Exception(
                "Ambiguity regarding {text_header} header: {atc_code}, {index}"
            )

        div = header.parent.find_next_sibling("div")
        res = get_sanitized_html_markdown_text(div)
    return res


def check_no_text_between_tables(outer_tables, index, atc):
    table_count = len(outer_tables)
    for i, table in enumerate(outer_tables):
        table_sibling = table.find_next_sibling()
        if table_sibling:
            if table_sibling.name != "table":
                is_last_table = i == table_count - 1
                if not is_last_table:
                    raise Exception(
                        "Text between non-nested tables in GFR section, modify script to account for this: {}, {}".format(
                            index, atc
                        )
                    )


def get_renal_info(soup, index, atc):
    final_res = "na"
    text_header = "Nedsat nyrefunktion"
    header = get_header(soup, text_header)
    if not header:
        return final_res

    div = header.parent.find_next_sibling("div")

    # has_nested_tables = []
    # has_regular_tables = []
    # has_no_tables = []
    tables = div.find_all("table")

    outer_tables = []
    first_table = div.find("table")
    if first_table:
        # print(index, atc)
        outer_tables = [first_table] + first_table.find_next_siblings("table")
        if len(outer_tables) != len(tables):
            # has_nested_tables.append(index)
            final_res = "Nested table - to be done manually"
        else:
            # has_regular_tables.append(index)
            # print_this = False
            final_res = ""
            check_no_text_between_tables(outer_tables, index, atc)
            for table in outer_tables:

                all_headers = table.find_all("tr", class_="Header")
                if len(all_headers) != 2:
                    raise Exception(
                        'For a table in "{}", the number of header rows != 2, modify script to account for this, index: {}, atc: {}'.format(
                            text_header, index, atc
                        )
                    )
                # general_header_soup = table.find("tr", class_="Header")
                general_header_text = get_sanitized_html_markdown_text(all_headers[0])
                headers_soup = all_headers[1]
                # headers_soup = general_header_soup.find_next_sibling("tr")
                headers = [header.get_text() for header in headers_soup.find_all("th")]

                content_soup = headers_soup.find_next_siblings("tr")
                rows = [
                    [cell for cell in row.find_all(["td", "th"])]
                    for row in content_soup
                ]
                res = general_header_text

                skip_cells = {}
                modified_rows = []
                for i, row in enumerate(rows):
                    new_row = []
                    for j, col in enumerate(row):

                        col_text = get_sanitized_html_markdown_text(col).rstrip("\n")
                        if not col_text:
                            col_text = "na"
                        new_row.append(col_text)

                        rowspan = col.get("rowspan")
                        if rowspan:
                            rowspan = int(rowspan)

                            for r in range(1, rowspan):
                                skip_cells[i + r, j] = col_text
                    modified_rows.append(new_row)
                new_modified_rows = []
                for k, row in enumerate(modified_rows):
                    new_modified_row = row.copy()
                    for i, j in skip_cells.keys():
                        if k == i:
                            new_text = skip_cells[i, j]
                            new_modified_row.insert(j, new_text)
                    new_modified_rows.append(new_modified_row)

                indent = 4 * " "
                for k, row in enumerate(new_modified_rows):
                    res_line = indent
                    if k > 0:
                        res_line += "\n" + indent
                    for j, col in enumerate(row):
                        header = headers[j]
                        if j > 0:
                            res_line += "\n" + indent
                        if header == "Advarsel" and col.count("\n") >= 1:
                            col_text = 2 * indent + col.replace("\n", "\n" + 2 * indent)
                            res_line += header + ":\n" + col_text.rstrip("\n")
                        else:
                            res_line += header + ": " + col
                    res += res_line + "\n"

                final_res += res + "\n\n"

            for table in tables:
                table.extract()
            text_without_tables = get_sanitized_html_markdown_text(div).rstrip("\n")
            final_res += text_without_tables
            # print("FINAL RES")
            # print(final_res, index, atc)

    else:
        # has_no_tables.append(index)
        final_res = get_sanitized_html_markdown_text(div)
    return final_res


def get_liver_info(soup, atc_code, index, text_header):

    # header = soup.find(lambda tag: tag.name == "h3" and text_header in tag.text)
    header = get_header(soup, text_header)

    res = "na"
    if header:
        if not header.text.strip() == text_header:
            raise Exception(
                "Ambiguity regarding {} header: {}, {}".format(
                    text_header, atc_code, index
                )
            )

        div = header.parent.find_next_sibling("div")
        res = get_sanitized_html_markdown_text(div)
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
    # print("{}, {} \n{}".format(index, atc, res))
    return res


def get_revision_date(soup, atc, index):
    text_header = "Revisionsdato"
    header = get_header(soup, text_header)
    markdown_text = H.handle(str(header.parent))
    pattern = r"\d{2}\.\d{2}\.\d{4}"
    res = re.findall(pattern, markdown_text)
    if len(res) != 1:
        raise Exception(
            "Ambiguity regarding {}: {}, {}".format(text_header, atc, index)
        )
    date = datetime.strptime(res[0], "%d.%m.%Y").date()
    return date


def remove_commas_between_bold(index, atc, markdown_text):
    # annoying_commas = ["** ,**", "** , **", "**, **"]
    # altered_markdown = markdown_text
    # for comma in annoying_commas:
    #     if comma in markdown_text:
    #         altered_markdown = altered_markdown.replace(comma, ",")
    #         print("ANNOYING COMMA WAS HERE: ", index, atc)
    # return altered_markdown
    comma_pattern = r"\*\*\s*,\s*\*\*"
    altered_markdown = markdown_text
    if re.search(comma_pattern, markdown_text):
        print("BOLD COMMA WAS HERE: ", index, atc)
        print(markdown_text)
        print("-----------------------")
        altered_markdown = re.sub(comma_pattern, ",", markdown_text)
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
        #     print(nb)
        #     print(new_nb)
        #     print("---------------")
    return res


def lower_non_copyright_pharma_forms(pharma_forms):
    copyright = "®"
    return [r.lower() if copyright not in r else r for r in pharma_forms]


def remove_last_period(pharma_forms):
    res = [f[:-1] if f[-1] == "." else f for f in pharma_forms]
    res = [r for r in res if r]
    return res


def get_all_bold(atc, index, markdown_text, pattern, exclusion_list):
    res = re.findall(pattern, markdown_text)
    res = [r for r in res if r not in exclusion_list]
    # res = [r.lower() for r in res if r not in exclusion_list]
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
    pattern = r"\*{2}(.*?)\*{2}"  # to detect markdown bold pattern, eg **Tabletter**

    # strings that appear in markdown as bold that don't count as pharma forms
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
    markdown_text = remove_commas_between_bold(index, atc, markdown_text)
    pharma_forms, contains_colored_tablets = get_all_bold(
        atc, index, markdown_text, pattern, exclusion_list
    )
    pharma_forms = lower_non_copyright_pharma_forms(remove_last_period(pharma_forms))

    # getting the matching non-bold text for each bold pharmaceutical form to be able to later to determine if film- eller sukkerovertrukne
    pharma_non_bold = get_all_non_bold(
        atc, index, markdown_text, pattern, exclusion_list, contains_colored_tablets
    )

    # using the matching bold and non_bold text to determine if the pharma form is additionally filmovertrukken, sukkerovertrukken, or overtrukken.
    new_pharma_forms = []
    if len(pharma_forms) != len(pharma_non_bold):
        raise Exception(
            "For {}: the list of bold text (pharmaceutical forms) and the list of non-bold (pharmaceutical form dosage) are not of equal length, ProMed must have been updated, update script to accomodate this: {}, {}".format(
                text_header, index, atc
            )
        )
    else:
        for bold, non_bold in zip(pharma_forms, pharma_non_bold):
            if any(s in non_bold for s in ["filmovertruk", "flmovertruk"]):
                # print("{}, {}, {}: {}".format(index, atc, bold, non_bold))
                new_pharma_forms.append(bold + ", filmovertrukne")
            elif "sukkerovertruk" in non_bold:
                new_pharma_forms.append(bold + ", sukkerovertrukne")
            elif "overtruk" in non_bold:
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
                basis["eGFR"] = get_renal_info(soup, index, l_atc)

                basis["Pharmaceutical form"], basis["Pharmaceutical form dosage"] = (
                    get_pharmaceutical_form(soup, l_atc, index)
                )
                basis["Revision date"] = get_revision_date(soup, l_atc, index)
                text_header_dict = {
                    "Doseringsforslag": "Dosage",
                    "Anvendelsesområder": "Registered indication",
                    "Kontraindikationer": "Contraindications",
                    "Forsigtighedsregler": "Warnings and precautions",
                }

                for text_header_danish, text_header_english in text_header_dict.items():
                    basis[text_header_english] = get_text(
                        soup, l_atc, index, text_header_danish
                    )
                basis["Dosereduction liver"] = get_liver_info(
                    soup, l_atc, index, "Nedsat leverfunktion"
                )

                basis["Halftime"] = get_halftime(soup, l_atc, index, "Farmakokinetik")

                # basis["eGFR"] = get_renal_info(soup, index, l_atc)

                return basis

            else:
                print("{}, not success or not long enough".format(index))
    except asyncio.TimeoutError:
        print("timeout error on index: ", index)


def expand_pharma_forms(input):
    forms_key = "Pharmaceutical form"
    amount_key = "Pharmaceutical form dosage"
    print(forms_key, amount_key)
    df = pd.DataFrame.from_dict(input)
    df = df.explode([forms_key, amount_key], ignore_index=True)
    return df


def remove_pharma_duplicates(pharma_expanded_df):
    # removes duplicate entries in list regarding atc and pharmaceutical form, keep the one with the latest date

    atc_key = "Atc"
    pharma_key = "Pharmaceutical form"
    date_key = "Revision date"
    index_key = "Index"
    df = pharma_expanded_df
    cols_to_print = ["Index", atc_key, pharma_key, date_key]
    # print(df[cols_to_print])
    df = df.sort_values([atc_key, index_key])
    df = df.sort_values(date_key).drop_duplicates([atc_key, pharma_key], keep="last")
    # print("\n-----------", df[cols_to_print])
    df = df.sort_values([atc_key, index_key], ascending=[True, True])
    # print("\n-----------", df[cols_to_print])
    return df


async def main(data, data_not_on_promed):
    timeout = aiohttp.ClientTimeout(total=6 * 60)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        scraping_res = await asyncio.gather(*[get(session, d) for d in data])
        only_res = [r for r in scraping_res if r]

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

        # removing pharmaceutical form dosage from final results, they were only used for getting correct pharmaceutical form
        final_pharma_df = pharma_duplicate_free_df.loc[
            :, pharma_duplicate_free_df.columns != "Pharmaceutical form dosage"
        ]
        print(final_pharma_df.columns)

        # adding empty entries for the atc codes not found on promed:
        for d in data_not_on_promed:
            na_text = "Not on ProMed"
            new_row = {"Index": na_text, "Active substance": d[0], "Atc": d[1]}
            start_index = len(new_row)
            for col in final_pharma_df.columns[start_index:]:
                new_row[col] = na_text
            # print(new_row)
            final_pharma_df = final_pharma_df._append(new_row, ignore_index=True)

        # print(final_pharma_df[-3:])
        final_pharma_df = final_pharma_df.sort_values(
            ["Atc", "Index"], ascending=[True, True]
        )
        final_pharma_df.to_csv(dst, index=False, escapechar=None)

        # cols_to_print = ["eGFR"]
        # print(final_pharma_df["eGFR"].loc[final_pharma_df.index[0]])

        # columns = final_res[0].keys()
        # write_to_csv_renal(
        #     final_res,
        #     columns,
        #     "working_example",
        # )


if __name__ == "__main__":
    data = get_all_data_with_indices()
    data_not_on_promed = get_data_not_on_promed()
    print("Atc's NOT ON PROMED: ", data_not_on_promed)
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
    indices = ["2765"]
    indices = ["521"]
    indices = ["4651"]
    # indices = ["2605", "8316", "9517"]
    # data_used = [d for d in data if d[5] in indices[0]]
    # print(data_used)
    data_used = data
    # data_used = [d for d in data if d[4] == "5965"]
    # print(data_used)
    asyncio.run(main(data_used, data_not_on_promed))
    end = perf_counter()

    # print(f"{len(data) / (end - start)} req/s")
    # print("total time: ", end - start)
