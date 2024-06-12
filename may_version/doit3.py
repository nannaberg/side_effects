from bs4 import BeautifulSoup
import asyncio
import aiohttp
from time import perf_counter
import cchardet
import lxml
import csv
import re
import html
from collections import defaultdict
from utils import *
from check_functions import *


# FILE = "bivirkninger_maj.txt"
SPECIAL_CASES_FILE = "blacklisted_sideeffects.txt"


def get_atc(soup):
    atc = soup.find(attrs={"name": "ATCkode"})
    if atc:
        return atc.next_sibling.b.text


def get_generic_name(soup, index):
    parent = soup.find(attrs={"class": "SpaceBtm IndholdsstofferHeaderLinks"})
    if parent == None:
        noparent = soup.find(
            title="Lægemidlet kan være helt udgået eller midlertidigt udgået pga. leveringssvigt"
        )
        print("In get_generic_name: Parent was none, index: ", index)
        print(noparent.text)
        return noparent.text
    children = parent.find_all("b")
    generic_name_list = []
    for b in children:
        generic_name_list.append(b.text)
    generic_name = ", ".join(generic_name_list)
    return generic_name


def get_all_side_effects(soup, index, atc, substrings):
    freqs = [
        "Meget almindelige (> 10 %)",
        "Almindelige (1-10 %)",
        "Ikke almindelige (0,1-1 %)",
        "Sjældne (0,01-0,1 %)",
        "Meget sjældne (< 0,01 %)",
        "Ikke kendt hyppighed",
    ]
    side_effect_dict = {k: [] for k in freqs}
    tables = soup.find_all("table", attrs={"class": "pipTable width100Procent"})
    table_present = False
    for t in tables:
        header = t.find("h3")
        if header and "Registrerede bivirkninger" in header.text:
            table_present = True
            tr_alternates = t.find_all("tr", attrs={"class": "TrAlternate"})
            for tr_alt in tr_alternates:
                freq = tr_alt.find("b").text
                for tr in tr_alt.find_next_siblings():
                    if tr.has_attr(
                        "class"
                    ):  # går igennem alle tr mellem nuværende frekvens-overskrift (også en tr) og næste frekvens-overskrift (også en tr)
                        break
                    side_effects = [td.text for td in tr.find_all("td")]
                    side_effects = [
                        # for cases like: Ventrikulære arytmier\r\n      \xa0(herunder torsades de pointes*)
                        y.strip()
                        for sublist in [
                            re.split(
                                r",\s*(?![^()]*\))",  # splitting string by comma excepting commas inside parentheses
                                " ".join(  # normalzing whitespace (eg two spaces become one space)
                                    x.replace("\xa0", " ")
                                    .replace("\r", "")
                                    .replace("\n", "")
                                    .replace("*", "")
                                    .split()
                                ),
                            )
                            for x in side_effects[
                                1:
                            ]  # removing "Systemorganklasse" field
                            if x
                        ]
                        for y in sublist
                    ]

                    side_effect_dict[freq].extend(side_effects)

                    # check_and_or(side_effects, index)
                    # check_weird_comma_splits(side_effects, index)
                    # check_weird_slash_cases(side_effects, index)
                    # check_weird_parentheses_cases(side_effects, index)

            if not any(side_effect_dict.values()):
                print(
                    "{}: header was present, but no sideefffects registered".format(
                        index
                    )
                )
            # print("side_effect_dict is empty: ", not any(side_effect_dict.values()))
    # if not table_present:
    #     print("index: {}, atc: {} had no side effect table".format(index, atc))
    return side_effect_dict


def get_present_side_effects_dict(
    side_effect_dict,
    sexual_side_effects,
    index,
    substrings,
    special_cases,
):
    present_sexual_side_effects = defaultdict(list)
    substrings_found = []  # substring pairs not part of the substrings list
    for freq in side_effect_dict.keys():
        for se in side_effect_dict[freq]:
            # super specific special case mainly just applicable for metabolske, may need to be expanded/adjusted for future extractions:
            if "hyper- eller hypoglykæmi" in se.lower():
                # print("Index: {} - FUNKY HYPERGLYKÆMI alert in {}".format(index, se))
                # se_old = se
                se = "Hyperglykæmi eller hypoglykæmi"
                # print("changing se from {} to {}".format(se_old, se))
            # if "symptomatisk hypotension" in se.lower():
            #     print(
            #         "index: {} - Symptomatisk hypotension was contained in mse: {}".format(
            #             index, se
            #         )
            #     )
            for sexual_se in sexual_side_effects:
                if sexual_se.lower() in se.lower():
                    include = True

                    if sexual_se.lower() != se.lower():

                        # case: if lse is a substring and one of its superstring is contained in mse -> don't include. The superstring, if it is present in listed_ses, will be registered when it appears as the lse (either as substring of something whitelisted or as itself)
                        lse_superstrings = get_lse_superstrings(sexual_se, substrings)
                        for lse_super in lse_superstrings:
                            if lse_super in se:
                                include = False
                        # old solution that did not do it correctly
                        # if (sexual_se, se) in substrings:
                        #     include = False
                        else:
                            substrings_found.append([int(index), sexual_se, se])
                            # case: (lse, mse) in special_cases: DON'T include lse
                            if (sexual_se, se) in special_cases:
                                include = False
                    if include:
                        present_sexual_side_effects[freq].append(sexual_se)

        # make sure all freqs present in the dict
        if freq not in list(present_sexual_side_effects.keys()):
            present_sexual_side_effects[freq] = []

    return (present_sexual_side_effects, substrings_found)


async def get(
    session: aiohttp.ClientSession,
    url: str,
    sexual_side_effects,
    substrings,
    special_cases,
):
    index = url[43:]
    try:
        async with session.get(url) as response:
            status = response.status
            length = response.content_length
            if status != 200 and status != 404:
                print("status was: {}, index was: {}".format(status, index))
            if status == 200 and length > 9000:
                data = await response.text()
                soup = BeautifulSoup(data, "lxml")
                atc = get_atc(soup)
                if int(index) % 100 == 0:
                    print(index, status, length)
                if atc:
                    side_effect_dict = get_all_side_effects(
                        soup, index, atc, substrings
                    )

                    # print("all sideeffects for {}\n".format(index))
                    # my_pprint(side_effect_dict)

                    if any(side_effect_dict.values()):
                        present_sexual_side_effects, substrings_found = (
                            get_present_side_effects_dict(
                                side_effect_dict,
                                sexual_side_effects,
                                index,
                                substrings,
                                special_cases,
                            )
                        )
                        if any(present_sexual_side_effects.values()):
                            generic_name = get_generic_name(soup, index)
                            return (
                                index,
                                atc,
                                generic_name,
                                present_sexual_side_effects,
                                substrings_found,
                            )
                else:
                    print("there was no atc, index: ", index)
    except asyncio.TimeoutError:
        print("timeout error on index: ", index)


# max 10543
# page but no medicine: len: 36431 and status code
# status code 302: page not found


async def main(n_reqs: int, file: str):
    sexual_side_effects = get_listed_sideeffects(file)
    special_cases = get_blacklisted_sideeffects(SPECIAL_CASES_FILE)
    substrings = None
    if "kardio" in file or "antichol" in file:
        print("!!special case of kardio/antichol!!")
        all_lses = get_listed_sideeffects("sideeffect_lists/bivirkninger_maj.txt")
        substrings = get_substrings(sexual_side_effects, all_lses)
    else:
        substrings = get_substrings(sexual_side_effects, sexual_side_effects)
    print(substrings)
    # print(sexual_side_effects)
    timeout = aiohttp.ClientTimeout(total=6 * 60)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        res = await asyncio.gather(
            *[
                get(session, url, sexual_side_effects, substrings, special_cases)
                for url in urls(n_reqs)
            ]
        )

        final_res = [r for r in res if r]
        # print("final res")
        # print(*final_res, sep=", ")
        print(
            "number of all medicines with sexual side effects: ",
            len(final_res),
        )
        write_to_csv(final_res, file)


def is_unique(uniques, index, atc, generic_name, side_effect_dict):
    for unique in uniques:
        u_index, u_atc, u_name, u_side_effect_dict = unique
        same_dict = all(
            set(u_side_effect_dict.get(key)) == set(side_effect_dict.get(key))
            for key in side_effect_dict.keys()
        )
        if u_atc == atc and u_name == generic_name and same_dict:
            return False
    else:
        return True


def write_to_csv(medicines, file):
    # sorting according to atc code
    medicines = sorted(medicines, key=lambda med: med[1])
    # print("medicines: ")
    # print(*medicines, sep=", ")
    uniques = []
    duplicates_total = 0
    with open(get_out_csv_file_name(file), "w") as f:
        all_substrings_found = []
        writer = csv.writer(f)
        headers = ["URL index", "ATC", "Generisk navn"]
        print("length: ", len(medicines))
        headers.extend(list(medicines[0][3].keys()))
        writer.writerow(headers)
        for index, atc, generic_name, side_effect_dict, substrings_found in medicines:
            if is_unique(uniques, index, atc, generic_name, side_effect_dict):
                uniques.append((index, atc, generic_name, side_effect_dict))
                row = []
                row.append(index)
                row.append(atc)
                row.append(generic_name)
                for h in headers[3:]:
                    ses = ", ".join(side_effect_dict[h])
                    row.append(ses)
                writer.writerow(row)
            else:
                duplicates_total += 1
            all_substrings_found.extend(substrings_found)
    print("number of duplicates found: ", duplicates_total)
    print(
        "total unique: {} =? {}: {}".format(
            len(uniques),
            len(medicines) - duplicates_total,
            len(uniques) == len(medicines) - duplicates_total,
        )
    )
    with open(get_found_substrings_file_name(file), "w") as f:
        unique_substring_dict = {}
        writer = csv.writer(f)
        all_substrings_found = sorted(all_substrings_found, key=lambda elm: int(elm[0]))
        # print(all_substrings_found[:10])
        for row in all_substrings_found:
            index, sse, se = row
            k = (sse, se)
            if k not in unique_substring_dict.keys():
                unique_substring_dict[k] = [1, [index]]
            else:
                unique_substring_dict[k][0] += 1
                unique_substring_dict[k][1].append(index)
        # print(unique_substring_dict)
        unique_substring_cases = []
        for key, value in unique_substring_dict.items():
            elm = [value[0]]
            elm.extend(list(key))
            elm.append(value[1])
            unique_substring_cases.append(elm)
        substring_header = [
            "Antal forekomster",
            "Listebivirkning",
            "Præparatbivirkning",
            "Url index for de præparater det forekommer i",
        ]
        writer.writerow(substring_header)
        for row in unique_substring_cases:
            writer.writerow(row)


def urls(n_reqs: int):
    single = False
    # single = True
    if single:
        url = "https://pro.medicin.dk/Medicin/Praeparater/{}".format(n_reqs)
        yield url
    else:
        for i in range(n_reqs):
            url = "https://pro.medicin.dk/Medicin/Praeparater/{}".format(i)
            yield url


if __name__ == "__main__":
    # n_reqs = 10800
    n_reqs = 11000  # the real one
    # n_reqs = 2951
    # n_reqs = 7780
    # n_reqs = 200

    args = sys.argv
    if len(args) <= 1:
        print("Need to provide a .txt file as argument")
    else:
        file = args[1]
        if not file.endswith(".txt"):
            print("Need to provide a .txt file as argument")
        else:
            start = perf_counter()
            asyncio.run(main(n_reqs, file))
            end = perf_counter()

            print(f"{n_reqs / (end - start)} req/s")
            print("total time: ", end - start)
