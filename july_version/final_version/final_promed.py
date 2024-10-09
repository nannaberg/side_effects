from drug_list_handling import get_all_data_with_indices
from bs4 import BeautifulSoup
import asyncio
import aiohttp
from time import perf_counter
from drug_list_handling import write_to_csv, write_to_csv_renal

# import requests
import lxml.html as lh
import lxml.etree as etree
import lxml
import html2text
from collections import Counter
from flockhart.flockhart import get_flockhart_dict, get_drug_isoforms


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
        # print(renal_div.prettify())
        inner_tables = []

        tables = renal_div.findAll("table")
        no_tables = len(tables)

        # if no_tables == 2:
        #     for table in tables:
        #         if table.findAll("table"):
        #             bool_inner_tables = True
        # if not tables:
        #     print("{}, {}: RENAL BUT NO TABLE".format(index, atc))
        for table in tables:
            all_inner_tables = table.findAll("table")
            if all_inner_tables:
                bool_inner_tables = True
                inner_tables.append(len(all_inner_tables))
            else:
                inner_tables.append(0)
        # print("{}, {}: table length: {}".format(index, atc, len(tables)))
        res = inner_tables
        # h = html2text.HTML2Text()
        # h.ignore_links = True
        # res = h.handle(str(renal_div))

    return (no_tables, bool_inner_tables, res)


def get_text(soup, atc_code, index, text_header):
    header = soup.find(lambda tag: tag.name == "h3" and text_header in tag.text)

    res = "na"
    if header:

        if not header.text.strip() == text_header:
            raise Exception(
                "Ambiguity regarding {text_header} header: {atc_code}, {index}"
            )

        div = header.parent.find_next_sibling("div")
        h = html2text.HTML2Text()
        h.ignore_links = True
        res = h.handle(str(div))
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
        h = html2text.HTML2Text()
        h.ignore_links = True
        res = h.handle(str(div))
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


def get_active_substances(soup, atc, index):
    active_substances = []
    parent = soup.find(attrs={"class": "SpaceBtm IndholdsstofferHeaderLinks"})
    if parent == None:
        noparent = soup.find(
            title="Lægemidlet kan være helt udgået eller midlertidigt udgået pga. leveringssvigt"
        )
        print("In get_generic_name: Parent was none, index: ", index)
        print(noparent.text)
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
    l_active_substance = data[0].lower()
    l_pharma_form = data[1]
    l_atc = data[2]
    l_name = data[3]
    index = data[4]
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
                basis["Atc"] = l_atc
                # basis = [index, l_atc]
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

                cyp_dict = get_cyp(soup, l_atc, index, flockhart_dict)
                for k, v in cyp_dict.items():
                    basis[k] = v
                basis["Halftime"] = get_halftime(soup, l_atc, index, "Farmakokinetik")
                # basis.append(get_halftime(soup, l_atc, index, "Farmakokinetik"))
                # basis.append(get_registered_indications(soup, l_atc, index))
                # get_liver_info(soup, l_atc, index)
                # basis.append(get_contraindications(soup, l_atc, index))
                # basis.append(get_renal_info(soup, l_atc, index))
                return basis
                # get_dose_reduction_info(soup, l_atc, index)

            else:
                print("{}, not success or not long enough".format(index))
    except asyncio.TimeoutError:
        print("timeout error on index: ", index)


async def main(data):
    timeout = aiohttp.ClientTimeout(total=6 * 60)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        flockhart_dict = get_flockhart_dict()
        res = await asyncio.gather(*[get(session, d, flockhart_dict) for d in data])

        final_res = [r for r in res if r]
        # tables_w_inner = [r for r in final_res if r[2][1]]
        # # print(*two_tables_wo_inner, sep="\n")
        # print("no pages with inner tables: ", len(tables_w_inner))
        # print(*tables_w_inner, sep="\n")

        # all_tables = [len(r[2]) if r[2] != "na" else r[2] for r in final_res]
        # print(Counter(all_tables))
        # print(all_tables)
        # for i in [2, 3, 7, 4]:
        #     for res in final_res:
        #         if len(res[2]) == i:
        #             print("{}, {}: {}".format(res[0], res[1], res[2]))
        #     print("--------------------")
        # for res in final_res:
        #     if res[2] == 3:
        #         print("{}, {}: {}", res[0], res[1], res[2])
        # for res in final_res:
        #     if res[2] == 7:
        #         print("{}, {}: {}", res[0], res[1], res[2])
        # for res in final_res:
        #     if res[2] == 1:
        #         print("{}, {}: {}", res[0], res[1], res[2])
        # print(all_tables)

        # columns = ["index", "atc", "registered indication", "renal_info"]
        columns = final_res[0].keys()
        # for k in final_res[0].keys:
        #     columns.append(k)
        # print("columns: ", columns)
        # columns = [
        #     "index",
        #     "atc",
        #     "registered indication",
        #     "contraindications",
        #     "warnings",
        #     "liver",
        #     "halftime",
        # ]
        # columns = ["index", "atc", "halftime"]
        write_to_csv_renal(
            final_res,
            columns,
            "working_example",
        )


if __name__ == "__main__":
    data = get_all_data_with_indices()
    # print(len(data))
    # print(*data[:10], sep="\n")

    start = perf_counter()
    # print(data[0])
    indices = ["4104", "5988", "5965", "9989"]
    indices = ["3380"]
    data_used = [d for d in data if d[4] in indices]
    data_used = data
    # data_used = [d for d in data if d[4] == "5965"]
    # print(data_used)
    asyncio.run(main(data_used))
    end = perf_counter()

    # print(f"{len(data) / (end - start)} req/s")
    # print("total time: ", end - start)
