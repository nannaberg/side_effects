import pandas as pd
from bs4 import BeautifulSoup
import asyncio
import aiohttp
from time import perf_counter


async def get(session: aiohttp.ClientSession, url: str):
    atc_code = url[42:]
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
                print(soup.table)

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

    atc_codes = ["C04AB01"]

    start = perf_counter()
    asyncio.run(main(atc_codes))
    end = perf_counter()

    print(f"{len(atc_codes) / (end - start)} req/s")
    print("total time: ", end - start)
