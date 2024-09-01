from drug_list_handling import get_all_data_with_indices
from bs4 import BeautifulSoup
import asyncio
import aiohttp
from time import perf_counter
from drug_list_handling import write_to_csv, write_to_csv_renal


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


def get_liver_info(soup, atc, index):
    header = soup.find(
        lambda tag: tag.name == "h3" and "Nedsat leverfunktion" in tag.text
    )
    if header:
        liver_div = header.parent.find_next_sibling("div")

        pure_text = remove_tags(liver_div)
        if "let" in pure_text:
            print("{}, {}:\n {}\n".format(index, atc, pure_text))
    else:
        # pass
        print("{}, {}, NO LIVER DOSE REDUCTION".format(index, atc))


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


def get_kidney_info(soup, atc, index):
    res = []
    renal_header = soup.find(
        lambda tag: tag.name == "h3" and "Nedsat nyrefunktion" in tag.text
    )
    if renal_header:
        kidney_div = renal_header.parent.find_next_sibling("div")
        table = kidney_div.find("table")
        ul = kidney_div.find("ul")

        if table:
            res.append("table")
        elif ul:

            # all_tags = [tag.name for tag in kidney_div.find_all(True)]
            # print("{}, {}: TABLE, tags: {}".format(index, atc, all_tags))
            res.append("ul")
        else:
            gfr_sections = kidney_div.find_all("p", class_="glob-padTop20")
            all_tags = list(set([tag.name for tag in kidney_div.find_all(True)]))
            # print("{}, {}: standard, all unique tags: {}".format(index, atc, all_tags))
            # if no glob-padTop20s:
            if not gfr_sections:
                # print("{}, {} HAS NO glob-padTop20 tag".format(index, atc))
                kidney_ps = kidney_div.find_all("p")
                for kidney_p in kidney_ps:
                    res.append(kidney_p.get_text(strip=True))

            for gfr_section in gfr_sections:
                first_section_text = gfr_section.text
                res.append(first_section_text)
                # kidney_text += first_section_text + sep
                # print("LINE: ", first_section_text)
                for sibling in gfr_section.find_next_siblings():
                    # print("CLASS: ", sibling.get("class"))
                    sibling_class_list = sibling.get("class")
                    if sibling_class_list:
                        if (
                            sibling_class_list[0] == "glob-padTop20"
                            or sibling_class_list[0] == "glob-padbtm20"
                        ):
                            # print("-------------")
                            res.append("\n")
                            break  # iterate through siblings until separator is encoutnered
                    else:
                        res.append(sibling.text)
            # print("---------------------------------------")

            # dealing with potentially relevant extra info after the calc
            calc_tag = kidney_div.find("div", class_="glob-padbtm20")
            # if index == "7402":
            #     print("7402:", calc_tag.prettify())
            if calc_tag:
                calc_siblings = calc_tag.findNextSiblings()
                # if calc_siblings:
                # print("LEN: ", len(calc_siblings))
                # print(calc_siblings.prettify())
                # if calc_siblings:
                #     # pass
                #     print("{}, {}: MORE SIBLNGS".format(index, atc))
                for calc_sib in calc_siblings:
                    if calc_sib.has_attr("class"):
                        # print("it had class")
                        # print(calc_sib.prettify())
                        if calc_sib["class"][0] != "referencer":
                            print("calc sib with class that is NOT referencer")
                            print(calc_sib.prettify())
                    else:
                        res.append(calc_sib.get_text(strip=True))
                        # print(
                        #     "{}, {}: MORE INFO, tag: {}".format(
                        #         index, atc, calc_sib.name
                        #     )
                        # )
                        # print("{}, {}: MORE INFO".format(index, atc))
                        # print(calc_sib.prettify())
                        # actually_all_tags = [
                        #     tag.name for tag in calc_sib.find_all(True)
                        # ]
                        # print(
                        #     "{}, {}: MORE INFO, all tags: {}".format(
                        #         index, atc, actually_all_tags
                        #     )
                        # )
                    # print("--------------------")
        # print("---------------------------------------")
        if res[-1] == "\n":
            res.pop()
        return res

    else:
        res.append("na")
    return res


def get_registered_indications(soup, atc_code, index):
    header = soup.find(
        lambda tag: tag.name == "h3" and "Anvendelsesområder" in tag.text
    )
    if not header.text.strip() == "Anvendelsesområder":
        raise Exception(
            "Ambiguity regarding registered indication header: {}, {}".format(
                atc_code, index
            )
        )

    reg_ind_div = header.parent.find_next_sibling("div")

    # sA = reg_ind_div.find(string=True).strip()

    all_uls = [tag.name for tag in reg_ind_div.find_all("ul")]

    uls = reg_ind_div.find_all("ul")
    for ul in uls:
        nested_ul = ul.find_all("ul")
        if nested_ul:
            print("{}, {} has nested uls".format(index, atc_code))
    # if len(all_uls) > 1:
    #     print("{}, {} has uls: {}".format(index, atc_code, all_uls))
    actually_all_tags = list(set([tag.name for tag in reg_ind_div.find_all(True)]))
    # testlist = ["a", "div", "p", "ul", "li"]
    # for act_tag in actually_all_tags:
    #     if act_tag not in testlist:
    #         print("{}, {}, {}".format(index, atc_code, actually_all_tags))
    #     break

    # if sA:
    #     print("{}, {}, has div text: {}".format(index, atc_code, sA))
    all_tags = reg_ind_div.find_all(["p", "li"])
    # print(len(all_tags))
    # print(*all_tags, sep="\n")

    res = remove_tags(reg_ind_div)

    reg_ind = []
    for tag in all_tags:
        text = tag.text.strip()
        # print("{}, {}".format(tag.name, text))
        # print(text)
        if text:
            reg_ind.append(text)

    # if len(reg_ind) > 0 and sA:
    #     print(
    #         "{}, {}, has p/li but also div text: {}".format(index, atc_code, repr(sA))
    #     )
    # print(len(reg_ind))
    # to_print = [(index, atc_code)] + reg_ind
    # print("\n".join(map(str, to_print)))
    # print("\n")
    # if len(reg_ind) < 1:
    #     print("{}, {}, no reg ind registered".format(index, atc_code))
    # else:
    #     print("\n{}, {}".format(index, atc_code))
    #     for i, reg in enumerate(reg_ind):
    #         print("{}: {}".format(i, reg))
    # print("{}, {}, Tags removed:".format(index, atc_code))
    # print(res)
    # print("\n")
    # # sA = reg_ind_div.find(string=True)
    # # print(sA)
    # s1 = " ".join(reg_ind_div.text.strip().split())  # to remove weird whitespace
    # print(s1)
    # s1 = s1.split("Se endvidere")[0].strip()
    # # print(s1)
    # reg_ind.append(s1)
    # print("now: ", reg_ind)
    # print("\n")
    # print("{}, {}:\n {}\n".format(index, atc_code, *reg_ind))
    # first_p = reg_ind_div.p
    # if first_p and first_p.text.strip():
    #     print("{}, {}, {}".format(atc_code, index, first_p.text.strip()))
    #     if first_p.find_next_sibling("p"):
    #         print("{}, {}, more ps".format(atc_code, index))


async def get(
    session: aiohttp.ClientSession,
    data: list,
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
    try:
        async with session.get(url) as response:
            status = response.status
            length = response.content_length
            if status == 200 and length > 9000:
                page = await response.text()
                soup = BeautifulSoup(page, "lxml")
                basis = [index, l_atc]
                get_registered_indications(soup, l_atc, index)
                # get_liver_info(soup, l_atc, index)

                basis.append(get_kidney_info(soup, l_atc, index))
                return basis
                # get_dose_reduction_info(soup, l_atc, index)

            else:
                print("{}, not success or not long enough".format(index))
    except asyncio.TimeoutError:
        print("timeout error on index: ", index)


async def main(data):
    timeout = aiohttp.ClientTimeout(total=6 * 60)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        res = await asyncio.gather(*[get(session, d) for d in data])

        final_res = [r for r in res if r]
        # print("final res", final_res)
        # print(
        #     "len(final_res):",
        #     len(final_res),
        # )
        # print("\nfinal results:")
        # print(*final_res, sep="\n")

        write_to_csv_renal(final_res, ["index", "atc", "renal_info"], "renal_info")
        # write_names_to_csv(final_res)


if __name__ == "__main__":
    data = get_all_data_with_indices()
    # print(len(data))
    # print(*data[:10], sep="\n")

    start = perf_counter()
    # print(data[0])
    data_used = [d for d in data if d[4] == "4104"]
    # print(data_used)
    asyncio.run(main(data_used))
    end = perf_counter()

    # print(f"{len(data) / (end - start)} req/s")
    # print("total time: ", end - start)
