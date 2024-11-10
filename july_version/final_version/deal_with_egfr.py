from bs4 import BeautifulSoup
import pandas as pd
from html_sanitizer import Sanitizer
import html2text
import re
from io import StringIO


sanitizer = Sanitizer()  # default configuration
H = html2text.HTML2Text()
H.ignore_links = True
H.body_width = 0
H.single_line_break = True

# Permanently changes the pandas settings
pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)
pd.set_option("display.width", None)
pd.set_option("display.max_colwidth", None)


def get_sanitized_html_markdown_text(soup):
    # print(soup.prettify())
    sanitized_html = sanitizer.sanitize(str(soup))

    markdown_text = H.handle(sanitized_html)
    return markdown_text


def get_all_egfr_html():
    df = pd.read_csv("renal_working_example.csv", keep_default_na=False)
    values = df.values.tolist()
    print(len(values))
    return [(x[0], x[1], x[-1]) for x in values if x[-1] != "na"]


def rec_parse_table(table):
    pass


def parse_table(table):
    # print(table.prettify())
    sep = " | "
    dfs = pd.read_html(StringIO(str(table)))
    for df in dfs:
        print(df)
        print("\n--------------------\n")
    outer_table = dfs[0]
    entries = []
    if len(dfs) > 1:
        # for i in range(1, len(dfs)):

        for j, row in outer_table.iterrows():
            nested_table = dfs[j + 1]
            nested_table_cols = nested_table.columns.to_list()
            nested_table_headers_string = " ".join(nested_table_cols)
            # print(nested_table.columns.to_list())
            entry = ""
            for col in outer_table.columns:

                val = row[col]
                if not val.startswith(nested_table_headers_string):
                    entry += val + sep
                else:

                    for k, n_row in nested_table.iterrows():
                        new_entry = entry
                        for n_col in nested_table_cols:
                            n_val = n_row[n_col]
                            new_entry += n_val + sep
                        entries.append(new_entry)
        for e in entries:
            print(e)
            print("\n")

    # print(len(dfs))
    # print(dfs[0])
    # print("---------\n")
    # print(dfs[1].columns)
    # df1_cols = " ".join(dfs[1].columns)
    # print(df1_cols)
    # for i in range(1, len(dfs)):
    #     print(dfs[i])
    #     print("----------------------\n")
    # print(dfs[1])
    # print("------------\n")
    # print(dfs[2])
    # print("------------\n")
    # print(dfs[3])
    # print("------------\n")
    # tr = table.find("tr")
    # all_trs = tr.find_next_siblings("tr")
    # ths = all_trs[0]
    # trs = all_trs[1:]
    # headers = [
    #     th_text
    #     for th_text in [get_sanitized_html_markdown_text(th) for th in ths]
    #     if th_text
    # ]
    # # print(headers)
    # first_tr = trs[0]
    # tds = first_tr.find_all("td")
    # print("rowspan: ", tds[0]["rowspan"])

    # for

    # print(all_trs)
    return 0


data = get_all_egfr_html()
indices = [2642]
indices = [1721]
indices = [79]
indices = [10609]
indices = [4323]
indices = [1132]
indices = [753]
indices = [7144]
indices = [8306]
indices = [4641]
indices = [957]
indices = [2025]
indices = [3540]
indices = [521]
indices = [4651]
# indices = [6567]
# indices = [4323]
# indices = [1237]
# data = [h for h in data if h[0] in indices]
has_nested_tables = []
has_regular_tables = []
has_no_tables = []


print(len(data))
no_tables = 0
for d in data:
    index = d[0]
    atc = d[1]
    html = d[2]

    soup = BeautifulSoup(html, "lxml")
    tables = soup.find_all("table")

    outer_tables = []
    first_table = soup.find("table")
    if first_table:
        # print(index, atc)
        outer_tables = [first_table] + first_table.find_next_siblings("table")
        if len(outer_tables) != len(tables):
            has_nested_tables.append(index)

        else:
            has_regular_tables.append(index)
            print_this = False
            table_res = ""
            table_count = len(outer_tables)
            for i, table in enumerate(outer_tables):
                table_sibling = table.find_next_sibling()
                if table_sibling:
                    if table_sibling.name != "table":
                        last = i == table_count - 1
                        if not last:
                            print(
                                "TAG: ",
                                index,
                                atc,
                                table_sibling.name,
                                last,
                                i,
                                table_count,
                            )
                general_header_soup = table.find("tr", class_="Header")
                general_header_text = get_sanitized_html_markdown_text(
                    general_header_soup
                )
                headers_soup = general_header_soup.find_next_sibling("tr")
                headers = [header.get_text() for header in headers_soup.find_all("th")]

                content_soup = headers_soup.find_next_siblings("tr")
                rows = [
                    [cell for cell in row.find_all(["td", "th"])]
                    for row in content_soup
                ]
                res = general_header_text

                if "Advarsel" in headers and headers[-1] != "Advarsel":
                    print("ADVARSEL PROBLEM", index, atc, headers)

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
                    keys_to_use = []
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

                            print_this = True

                            col_text = 2 * indent + col.replace("\n", "\n" + 2 * indent)
                            res_line += header + ":\n" + col_text.rstrip("\n")
                        else:
                            res_line += header + ": " + col
                    res += res_line + "\n"

                table_res += res + "\n\n"
            if print_this:
                print(index, atc)
                print(table_res)
                print("------------------")

            # print("--------------------------NEXT---------------------------------")
    else:
        has_no_tables.append(index)
        markdown_text = get_sanitized_html_markdown_text(soup)

    for table in soup.find_all("table"):
        table.extract()
    text_without_tables = get_sanitized_html_markdown_text(soup).rstrip("\n")
    if (
        text_without_tables
        and index not in has_no_tables
        and index not in has_nested_tables
    ):
        print(text_without_tables)
    # print(index, atc, repr(text_without_tables))
    # print("---------------------------------------------")
    # print(index, atc)
    # print(markdown_text)
    # print("------------------------\n")

print("has regular tables: ", len(has_regular_tables))
print("has nested tables: ", len(has_nested_tables))
print("has no tables: ", len(has_no_tables))

# if first_table:
#     outer_tables = [first_table] + first_table.find_next_siblings("table")
#     if (len(tables) - len(outer_tables)) > 1:  # more than one nested table
#         print(index, atc, len(tables), len(outer_tables))

# if first_table:
#     print(index, atc)
#     outer_table_header = get_sanitized_html_markdown_text(first_table.find("h3"))

#     print(outer_table_header)
#     outer_tables = [first_table] + first_table.find_next_siblings("table")
#     # outer_tables = first_div.select('div' > 'table')
#     parse_table(outer_tables[0])

#     print(len(outer_tables))
# else:
#     no_tables += 1
# print("--------------------")
print("PAGES WITH NO TABLES: ", no_tables)
