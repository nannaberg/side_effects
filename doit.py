from bs4 import BeautifulSoup
import asyncio
import aiohttp
from time import perf_counter
import cchardet
import lxml
import csv
import re

FILE = "seksuelle_lægemiddelbivirkninger.txt"


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


def get_all_side_effects(soup, index, atc):
    all_side_effects = []

    tables = soup.find_all("table", attrs={"class": "pipTable width100Procent"})
    for t in tables:
        header = t.find("h3")
        if header and "Registrerede bivirkninger" in header.text:
            trs = t.find_all("tr", attrs={"class": None})
            for tr in trs:
                side_effects = [td.text for td in tr.find_all("td")]
                # print("first side_effects: ", side_effects)
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
                        for x in side_effects[1::]  # removing "Systemorganklasse" field
                        if x
                    ]
                    for y in sublist
                ]
                # print("next  side_effects: ", side_effects)
                # print("")
                all_side_effects.append(side_effects)
            return all_side_effects
    print("index: {}, atc: {} had no side effect table".format(index, atc))


def get_present_side_effects(all_side_effects, sexual_side_effects, index, substrings):
    present_sexual_side_effects = []
    for ses in all_side_effects:
        for se in ses:
            for sexual_se in sexual_side_effects:
                # print(sexual_se)
                # if sexual_se in se and sexual_se != se:
                #     print(
                #         "index: {}, sexual_se: {}, se: {}".format(index, sexual_se, se)
                #     )
                # check om
                if sexual_se.lower() in se.lower():
                    # print("was included: ", sexual_se)
                    present_sexual_side_effects.append(sexual_se)
                for se1, se2 in substrings:
                    if all(se in present_sexual_side_effects for se in [se1, se2]):
                        print("")
                        print("before removing: ", present_sexual_side_effects)
                        present_sexual_side_effects.remove(se1)
                        print("after removing: ", present_sexual_side_effects)
                        print("")
        # print("")
    return present_sexual_side_effects



# semaphore = asyncio.Semaphore(100)


async def get(
    session: aiohttp.ClientSession, url: str, sexual_side_effects, substrings
):
    index = url[43:]
    # async with semaphore:
    try:
        async with session.get(url) as response:
            status = response.status
            length = response.content_length
            if status == 200 and length > 9000:
                data = await response.text()
                soup = BeautifulSoup(data, "lxml")
                atc = get_atc(soup)
                if int(index) % 100 == 0:
                    print(index, status, length)
                if atc:
                    all_side_effects = get_all_side_effects(soup, index, atc)
                    if all_side_effects:
                        present_sexual_side_effects = get_present_side_effects(
                            all_side_effects, sexual_side_effects, index, substrings
                        )
                        if len(present_sexual_side_effects) > 0:
                            generic_name = get_generic_name(soup)
                            return (
                                index,
                                atc,
                                generic_name,
                                list(set(present_sexual_side_effects)),
                            )
                else:
                    print("there was no atc, index: ", index)
            # else:
            #     print("status was not 200: ", status)
    except asyncio.TimeoutError:
        print("timeout error on index: ", url[43:])


# max 10543
# page but no medicine: len: 36431 and status code
# status code 302: page not found
# medicin ialt: 3630 præparater


async def main(n_reqs: int):
    sexual_side_effects = get_sexual_side_effects(FILE)
    substrings = []
    for se in sexual_side_effects:
        for se2 in sexual_side_effects:
            if se != se2 and se in se2:
                substrings.append((se, se2))
    print(substrings)
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
            "number of all medicines sexual side effects: ",
            len(final_res),
        )

        write_to_csv(final_res)


def write_to_csv(medicines):
    # sorting according to atc kode
    medicines = sorted(medicines, key=lambda med: med[1])

    uniques = []
    with open("database.csv", "w") as f1, open("database_with_urls.csv", "w") as f2:
        max_number_of_ses = max([len(med[3]) for med in medicines])
        writer1 = csv.writer(f1)
        writer2 = csv.writer(f2)
        writer1_headers = ["ATC", "Generisk navn"]
        writer2_headers = ["URL index", "ATC", "Generisk navn"]
        ses_headers = ["Seksuel bivirkning"] * max_number_of_ses
        writer1_headers.extend(ses_headers)
        writer2_headers.extend(ses_headers)
        writer1.writerow(writer1_headers)
        writer2.writerow(writer2_headers)

        for index, atc, generic_name, side_effects in medicines:
            if (atc, generic_name, side_effects) not in uniques:
                if len(side_effects) > max_number_of_ses:
                    max_number_of_ses = len(side_effects)
                row = []
                row.append(atc)
                row.append(generic_name)
                row.extend(side_effects)
                writer1.writerow(row)
                # row.insert(
                #     0, "https://pro.medicin.dk/Medicin/Praeparater/{}".format(index)
                # )
                row.insert(0, index)
                writer2.writerow(row)
                uniques.append((atc, generic_name, side_effects))
    print(
        "unique medicine length: {}, non-unique length: {}".format(
            len(uniques), len(medicines)
        )
    )

def urls(n_reqs: int):
    for i in range(n_reqs):
        url = "https://pro.medicin.dk/Medicin/Praeparater/{}".format(i)
        yield url


if __name__ == "__main__":
    n_reqs = 10800
    # n_reqs = 5000
    # n_reqs = 500

    start = perf_counter()
    asyncio.run(main(n_reqs))
    end = perf_counter()

    print(f"{n_reqs / (end - start)} req/s")
    print("total time: ", end - start)
