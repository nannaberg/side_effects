import pandas as pd
from bs4 import BeautifulSoup
import asyncio
import aiohttp
from time import perf_counter
from drug_list_handling import get_atc_codes


def make_ddd_dict(ddd, u, admR, note):
    return {"DDD": ddd, "U": u, "AdmR": admR, "Note": note}


def check_duplicate_admR_and_notes(ddd_dict_list, atc_code):
    admRs_notes = [(d["AdmR"], d["Note"]) for d in ddd_dict_list]
    seen = []
    duplicates = []
    for admR, _ in admRs_notes:
        if admR in seen and admR not in duplicates:
            duplicates.append(admR)
        else:
            seen.append(admR)
    to_print = []
    for admR, note in admRs_notes:
        if admR in duplicates:
            to_print.append((atc_code, admR, note))
    if to_print:
        print(*to_print, sep="\n")


def check_empty_spots(ddd_dict_list, atc_code):
    admRs = [d["AdmR"] for d in ddd_dict_list]
    # units = [d["U"] for d in ddd_dict_list]
    # ddd = [d["DDD"] for d in ddd_dict_list]

    if (
        "" in admRs
    ):  # this check catches all empty cases, no need for units and ddd checks
        print("{}, {}: {}".format(atc_code, "admR", admRs))
    # if "" in units:
    #     print("{}, {}: {}".format(atc_code, "units", units))
    # elif "" in ddd:
    #     print("{}, {}: {}".format(atc_code, "ddd", units))


async def get(session: aiohttp.ClientSession, url: str):
    atc_code = url[42:]
    try:
        async with session.get(url) as response:
            status = response.status
            if status == 200:
                page = await response.text()
                soup = BeautifulSoup(page, "lxml")
                atc_td = soup.find(
                    lambda tag: tag.name == "td" and "ATC code" in tag.text
                )
                all_trs = atc_td.parent.find_next_siblings("tr")
                # if len(all_trs) > 1:
                #     print("{}: {}".format(atc_code, len(all_trs)))
                # print(len(all_trs))
                ddd_dict_list = []
                for tr in all_trs:
                    all_tds = tr.find_all("td")
                    ddd = all_tds[2].text.strip()
                    u = all_tds[3].text.strip()
                    admR = all_tds[4].text.strip()
                    note = all_tds[5].text.strip()
                    ddd_dict_list.append(make_ddd_dict(ddd, u, admR, note))
                # print(*ddd_dict_list)
                # check_empty_spots(ddd_dict_list, atc_code)
                # check_duplicate_admR_and_notes(ddd_dict_list, atc_code)

                # if len(all_trs) < 1:
                #     raise Exception("table ambiguity for atc: {}".format(atc_code))
                return (atc_code, ddd_dict_list)
            else:
                print("atc: {} did not exist!", atc_code)
    except asyncio.TimeoutError:
        print(
            "timeout error on index: ",
        )
    return 0


def urls(atc_codes: int):
    for atc_code in atc_codes:
        url = "https://atcddd.fhi.no/atc_ddd_index/?code={}".format(atc_code)
        yield url


async def main(atc_codes: int):
    timeout = aiohttp.ClientTimeout(total=6 * 60)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        res = await asyncio.gather(*[get(session, url) for url in urls(atc_codes)])

        final_res = [r for r in res if r]
        # print(
        #     "len(final_res):",
        #     len(final_res),
        # )
        print(*final_res, sep="\n")
        # print("\nfinal results:")
        # print(*final_res, sep="\n")
        # write_to_csv(final_res)
        # write_names_to_csv(final_res)


if __name__ == "__main__":

    atc_codes = ["C04AB01"]

    atc_codes = get_atc_codes()
    # print(*atc_codes, sep="\n")

    start = perf_counter()
    asyncio.run(main(atc_codes))
    end = perf_counter()

    print(f"{len(atc_codes) / (end - start)} req/s")
    print("total time: ", end - start)
