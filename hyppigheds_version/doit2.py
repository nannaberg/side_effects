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

FILE = "bivirkninger_marts.txt"


def get_sexual_side_effects(FILE):
    with open(FILE) as f:
        return sorted(
            list(
                set([" ".join(line.split()) for line in f.read().splitlines() if line])
            )
        )


def get_atc(soup):
    atc = soup.find(attrs={"name": "ATCkode"})
    if atc:
        return atc.next_sibling.b.text


def get_generic_name(soup):
    parent = soup.find(attrs={"class": "SpaceBtm IndholdsstofferHeaderLinks"})
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
    for t in tables:
        header = t.find("h3")
        if header and "Registrerede bivirkninger" in header.text:
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
    return side_effect_dict


def get_present_side_effects_dict(
    side_effect_dict, sexual_side_effects, index, substrings
):
    present_sexual_side_effects = defaultdict(list)
    for freq in side_effect_dict.keys():
        for se in side_effect_dict[freq]:
            for sexual_se in sexual_side_effects:
                if sexual_se.lower() in se.lower():
                    # if sexual_se.lower() != se.lower():
                    #     print("s1: ", sexual_se)
                    #     print("s2: ", se)
                    #     print("")
                    # if sexual_se != se:
                    #     print(
                    #         "index: {}, sexual_se: {}, se: {}".format(
                    #             index, sexual_se, se
                    #         )
                    #     )
                    present_sexual_side_effects[freq].append(sexual_se)

        # remove substrings (eg remove Infertilitet hvis Irreversibel infertilitet is present):
        for se1, se2 in substrings:
            if all(se in present_sexual_side_effects[freq] for se in [se1, se2]):
                # print(
                #     "index: {}, before removing: {}".format(
                #         index, present_sexual_side_effects[freq]
                #     )
                # )
                present_sexual_side_effects[freq].remove(se1)
                # print(
                #     "index: {}, after removing: {}".format(
                #         index, present_sexual_side_effects[freq]
                #     )
                # )
                # print("")
        # make sure all freqs present in the dict
        if freq not in list(present_sexual_side_effects.keys()):
            present_sexual_side_effects[freq] = []

    return present_sexual_side_effects


async def get(
    session: aiohttp.ClientSession, url: str, sexual_side_effects, substrings
):
    index = url[43:]
    try:
        async with session.get(url) as response:
            status = response.status
            length = response.content_length
            if status == 200 and length > 9000:
                data = await response.text()
                soup = BeautifulSoup(data, "lxml")
                atc = get_atc(soup)
                if int(index) % 50 == 0:
                    print(index, status, length)
                if atc:
                    side_effect_dict = get_all_side_effects(
                        soup, index, atc, substrings
                    )

                    if any(side_effect_dict.values()):
                        present_sexual_side_effects = get_present_side_effects_dict(
                            side_effect_dict, sexual_side_effects, index, substrings
                        )
                        if any(present_sexual_side_effects.values()):
                            generic_name = get_generic_name(soup)
                            return (
                                index,
                                atc,
                                generic_name,
                                present_sexual_side_effects,
                            )
                else:
                    print("there was no atc, index: ", index)
    except asyncio.TimeoutError:
        print("timeout error on index: ", url[43:])


# max 10543
# page but no medicine: len: 36431 and status code
# status code 302: page not found


async def main(n_reqs: int):
    sexual_side_effects = get_sexual_side_effects(FILE)
    substrings = []
    for se in sexual_side_effects:
        for se2 in sexual_side_effects:
            if se.lower() != se2.lower() and se.lower() in se2.lower():
                substrings.append((se, se2))
    # print(substrings)
    # print(sexual_side_effects)
    timeout = aiohttp.ClientTimeout(total=6 * 60)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        res = await asyncio.gather(
            *[
                get(session, url, sexual_side_effects, substrings)
                for url in urls(n_reqs)
            ]
        )

        final_res = [r for r in res if r]
        print(
            "number of all medicines with sexual side effects: ",
            len(final_res),
        )
        write_to_csv(final_res)


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


def write_to_csv(medicines):
    # sorting according to atc code
    medicines = sorted(medicines, key=lambda med: med[1])
    uniques = []
    duplicates_total = 0
    with open("database2.csv", "w") as f:
        writer = csv.writer(f)
        headers = ["URL index", "ATC", "Generisk navn"]
        print("length: ", len(medicines))
        headers.extend(list(medicines[0][3].keys()))
        writer.writerow(headers)
        for index, atc, generic_name, side_effect_dict in medicines:
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
    print("number of duplicates found: ", duplicates_total)


def urls(n_reqs: int):
    # url = "https://pro.medicin.dk/Medicin/Praeparater/{}".format(n_reqs)
    # yield url
    for i in range(n_reqs):
        url = "https://pro.medicin.dk/Medicin/Praeparater/{}".format(i)
        yield url


if __name__ == "__main__":
    n_reqs = 10800  # the real one
    # n_reqs = 448
    # n_reqs = 6848

    start = perf_counter()
    asyncio.run(main(n_reqs))
    end = perf_counter()

    print(f"{n_reqs / (end - start)} req/s")
    print("total time: ", end - start)


# for x in side_effects:
#     if x:
#         x_without_danish = (
#             x.replace("æ", "")
#             .replace("æ", "")
#             .replace("å", "")
#             .replace(" ", "")
#         )
#         # print(x_without_danish.lower())
#         if not x_without_danish.lower().isalpha():
#             print("index: {}, se: {}".format(index, x))


# all_side_effects = [i for row in side_effect_dict.values() for i in row]
# for se1, se2 in substrings:
#     if se1 in all_side_effects:
#         print("{}, se1: {}".format(index, se1))
#     if se2 in all_side_effects:
#         print("{}, se2: {}".format(index, se2))
#     if se1 in all_side_effects and se2 in all_side_effects:
#         print("index {}, se1: {}, se2: {}".format(index, se1, se2))

# print("Duplicate found")
# print("u_index: {}, index: {}".format(u_index, index))
# print("u_atc: {}, atc: {}".format(u_atc, atc))
# print("u_name: {}, generic_name: {}".format(u_name, generic_name))
# for k in side_effect_dict.keys():
#     print(
#         "u_ses: {}, ses: {}".format(
#             u_side_effect_dict[k], side_effect_dict[k]
#         )
#     )
# print("\n")
