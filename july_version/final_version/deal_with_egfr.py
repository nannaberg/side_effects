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
# indices = [6567]
# indices = [4323]
# indices = [1237]
data = [h for h in data if h[0] in indices]
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
    # if len(tables) > 1:
    #     print(index, atc, len(tables))
    # print(soup)

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
            for table in outer_tables:
                # print(index, atc)
                general_header_soup = table.find("tr", class_="Header")
                general_header_text = get_sanitized_html_markdown_text(
                    general_header_soup
                )
                headers_soup = general_header_soup.find_next_sibling("tr")
                headers = [header.get_text() for header in headers_soup.find_all("th")]
                # print(general_header_text)
                # print(headers)

                content_soup = headers_soup.find_next_siblings("tr")
                rows = [
                    [cell for cell in row.find_all(["td", "th"])]
                    for row in content_soup
                ]
                res = general_header_text
                # print(index, atc)
                # to_unmerge = []

                skip_cells = {}
                modified_rows = []
                for i, row in enumerate(rows):
                    new_row = []
                    for j, col in enumerate(row):

                        # if (i, j) in skip_cells.keys():
                        # print("in skipcells: ", i, j, skip_cells[i, j])
                        # new_row.append(" " * len(skip_cells[i, j]))

                        col_text = get_sanitized_html_markdown_text(col).rstrip("\n")
                        if not col_text:
                            col_text = "na"
                        new_row.append(col_text)
                        # print(i, j, col_text)

                        rowspan = col.get("rowspan")
                        if rowspan:
                            print_this = True
                            rowspan = int(rowspan)

                            for r in range(1, rowspan):
                                skip_cells[i + r, j] = col_text
                    modified_rows.append(new_row)
                new_modified_rows = []
                print(skip_cells.keys())
                for k, row in enumerate(modified_rows):
                    keys_to_use = []
                    # print(row)
                    new_modified_row = row.copy()
                    for i, j in skip_cells.keys():
                        if k == i:
                            new_text = skip_cells[i, j]
                            # print(i, j, new_text)
                            new_modified_row.insert(j, new_text)
                    print(k, new_modified_row)
                    new_modified_rows.append(new_modified_row)
                    # new_row = []
                    # rowspan = 0
                    # for j, col in enumerate(row):

                    #     if (i, j) in skip_cells.keys():
                    #         # new_row.append(" " * len(skip_cells[i, j]))
                    #         new_row.append(skip_cells[i, j])

                    #     col_text = get_sanitized_html_markdown_text(col).rstrip("\n")
                    #     if not col_text:
                    #         col_text = "na"
                    #     new_row.append(col_text)
                    #     rowspan = col.get("rowspan")
                    #     if rowspan:
                    #         print_this = True
                    #         rowspan = int(rowspan)
                    #         print("ROWSPAN: ", rowspan)
                    #         for r in range(1, rowspan):
                    #             # goal:
                    #             # skip_cells.append((i + len(modified_rows) + r, j))
                    #             skip_index = (i + len(modified_rows) + r, j)
                    #             print(skip_index)
                    #             skip_cells[i + len(modified_rows) + r, j] = col_text
                    #             # print(skip_cells)
                    # modified_rows.append(new_row)

                # if print_this:
                #     print(index, atc)
                #     for row in modified_rows:
                #         for col in row:
                #             print(col)
                #         print("\n")

                for row in new_modified_rows:
                    for j, col in enumerate(row):
                        header = headers[j]
                        if j > 0:
                            res += " | "
                        # col_text = headers[j] + ": " + col
                        if col.isspace():
                            res += " " * len(header + ": ") + col
                        else:
                            if col.count("\n") >= 2:
                                # print(repr(col))
                                skip_space = len(res.split("\n")[0]) + len(
                                    header + ": "
                                )
                                col_text = col.replace("\n", "\n" + " " * skip_space)
                                res += header + ": " + col_text
                            else:
                                res += header + ": " + col
                    res += "\n"

                table_res += res + "\n\n"
            if print_this:
                print(index, atc)
                print(table_res)
                print("------------------")
            # for table in outer_tables:
            #     # print(index, atc)
            #     general_header_soup = table.find("tr", class_="Header")
            #     general_header_text = get_sanitized_html_markdown_text(
            #         general_header_soup
            #     )
            #     headers_soup = general_header_soup.find_next_sibling("tr")
            #     headers = [header.get_text() for header in headers_soup.find_all("th")]
            #     # print(general_header_text)
            #     # print(headers)

            #     content_soup = headers_soup.find_next_siblings("tr")
            #     rows = [
            #         [cell for cell in row.find_all(["td", "th"])]
            #         for row in content_soup
            #     ]
            #     res = general_header_text
            #     # print(index, atc)
            #     # to_unmerge = []

            #     skip_cells = {}
            #     modified_rows = []
            #     for i, row in enumerate(rows):
            #         new_row = []
            #         rowspan = 0
            #         for j, col in enumerate(row):

            #             if (i, j) in skip_cells.keys():
            #                 # new_row.append(" " * len(skip_cells[i, j]))
            #                 new_row.append(skip_cells[i, j])

            #             col_text = get_sanitized_html_markdown_text(col).rstrip("\n")
            #             if not col_text:
            #                 col_text = "na"
            #             new_row.append(col_text)
            #             rowspan = col.get("rowspan")
            #             if rowspan:
            #                 print_this = True
            #                 rowspan = int(rowspan)
            #                 print("ROWSPAN: ", rowspan)
            #                 for r in range(1, rowspan):
            #                     # goal:
            #                     # skip_cells.append((i + len(modified_rows) + r, j))
            #                     skip_index = (i + len(modified_rows) + r, j)
            #                     print(skip_index)
            #                     skip_cells[i + len(modified_rows) + r, j] = col_text
            #                     # print(skip_cells)
            #         modified_rows.append(new_row)

            #     if print_this:
            #         print(index, atc)
            #         for row in modified_rows:
            #             for col in row:
            #                 print(col)
            #             print("\n")

            #     for row in modified_rows:
            #         for j, col in enumerate(row):
            #             header = headers[j]
            #             if j > 0:
            #                 res += " | "
            #             # col_text = headers[j] + ": " + col
            #             if col.isspace():
            #                 res += " " * len(header + ": ") + col
            #             else:
            #                 res += header + ": " + col
            #         res += "\n"

            #     table_res += res + "\n\n"
            # if print_this:
            #     print(index, atc)
            #     print(table_res)
            #     print("-------------------------")
            # print(" | ".join(row))
            # for row in
            # res += "\n"
            # print(res)
            # df = pd.read_html(StringIO(str(table)))[0]
            # level0_headers = list(set(df.columns.get_level_values(0).tolist()))
            # overarching_header = level0_headers[0]
            # df = df.droplevel(0, axis=1)
            # headers = df.columns

            # # print(headers)

            # # headers = df.columns.get_level_values(1)
            # # print(overarching_header)
            # # print(headers)
            # print(index, atc)
            # # print(df)
            # res = overarching_header + "\n"
            # df = df.fillna("na")
            # for i in df.index:
            #     first = True
            #     for col in headers:
            #         if not first:
            #             res += " | "
            #         first = False
            #         val = df[col][i]
            #         res += col + ": " + val

            #     res += "\n"
            # print(res)
            # for i, row in df.iterrows():
            #     print(row)
            #     for col in headers:
            #         print(row[col])
            # print(df[0].info())
            # if len(df) > 1:
            #     print("NOOOOOOOOOOOOO")
            # rows = df[0].shape[0]
            # if rows > 1:
            #     print(index, atc)
            #     print(df[0])
            #     text_version = df[0].to_string(index=False)
            #     print(text_version)
            #     print(repr(text_version))
            #     # markdown_tabel = get_sanitized_html_markdown_text(table)
            #     # print(markdown_tabel)
            #     print("\n")
            # print("--------------------------NEXT---------------------------------")
    else:
        has_no_tables.append(index)
        markdown_text = get_sanitized_html_markdown_text(soup)

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
