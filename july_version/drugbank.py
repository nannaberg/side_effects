import pandas as pd
from bs4 import BeautifulSoup
import asyncio
import aiohttp
from time import perf_counter


SRC = "docs1/All_drugs_DK_all formulations_checked_if_priority_ongoing_130624.xlsx"


def get_all_data(file):
    # read by default 1st sheet of an excel file
    df = pd.read_excel(file)
    return df.values.tolist()


def get_atc_codes(file):
    all_data = get_all_data(file)
    data = [x[3] for x in all_data if x[0] == "X"]
    return list(set(data))


async def get(session: aiohttp.ClientSession, url: str):
    # atc_code = url[42:]
    atc_code = url[28:]
    # "https://go.drugbank.com/atc/G03BA03"
    print(atc_code)
    try:
        async with session.get(url) as response:
            status = response.status
            length = response.content_length
            print(length)
            if status == 200:
                print("success!")
                page = await response.text()
                soup = BeautifulSoup(page, "lxml")
                drug = soup.find(id=atc_code)
                print(drug)
                # enzymes = soup.find(id="enzymes")
                # # print(enzymes.strong)
                # bla = enzymes.find_all(string="Cytochrome P450 3A5")

                # print("bla: ", bla[0].parent.parent)
                # print(enzymes)
                # "Cytochrome P450 3A5"

    except asyncio.TimeoutError:
        print(
            "timeout error on index: ",
        )
    return 0


def urls(atc_codes: int):
    print("# of atc codes: ", len(atc_codes))
    for atc_code in atc_codes:
        url = "https://go.drugbank.com/atc/{}".format(atc_code)
        print(url)
        yield url


async def main(atc_codes: int):
    timeout = aiohttp.ClientTimeout(total=6 * 60)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        res = await asyncio.gather(*[get(session, url) for url in urls(atc_codes)])

        final_res = [r for r in res if r]
        print(
            "len(final_res):",
            len(final_res),
        )
        print(final_res)
        # print("\nfinal results:")
        # print(*final_res, sep="\n")
        # write_to_csv(final_res)
        # write_names_to_csv(final_res)


if __name__ == "__main__":

    # idxs = ["00199"]
    # atc_codes = get_atc_codes(SRC)[:20]
    atc_codes = ["G03BA03"]

    start = perf_counter()
    asyncio.run(main(atc_codes))
    end = perf_counter()

    print(f"{len(atc_codes) / (end - start)} idxs/s")
    print("total time: ", end - start)
