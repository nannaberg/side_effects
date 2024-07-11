import pandas as pd
from bs4 import BeautifulSoup
import asyncio
import aiohttp
from time import perf_counter

SRC = "docs1/All_drugs_DK_all formulations_checked_if_priority_ongoing_130624.xlsx"
DST = "drugs_with_indices.csv"


def get_data(file):
    # read by default 1st sheet of an excel file
    df = pd.read_excel(file)
    all_data = df.values.tolist()
    data = [(x[3], x[4]) for x in all_data if x[0] == "X"]
    return data


def urls(n_reqs: int, single):
    if single:
        url = "https://pro.medicin.dk/Medicin/Praeparater/{}".format(n_reqs)
        yield url
    else:
        for i in range(n_reqs):
            url = "https://pro.medicin.dk/Medicin/Praeparater/{}".format(i)
            yield url


def get_atc(soup):
    atc = soup.find(attrs={"name": "ATCkode"})
    if atc:
        return atc.next_sibling.b.text


def get_name(soup):
    title = soup.find(attrs={"class": "ptitle"})
    title = title.text.strip().replace("®", "")
    num_index = next((i for i, c in enumerate(title) if c.isdigit()), len(title))
    if num_index:
        title = title[:num_index].strip()
    return title


async def get(
    session: aiohttp.ClientSession,
    url: str,
    data: list,
):
    index = url[43:]
    try:
        async with session.get(url) as response:
            status = response.status
            length = response.content_length
            if status == 200 and length > 9000:
                page = await response.text()
                soup = BeautifulSoup(page, "lxml")
                m_atc = get_atc(soup)
                # if int(index) % 100 == 0:
                #     print(index, status, length)
                if m_atc:
                    m_name = get_name(soup)

                for l_atc, l_name in data:
                    if m_atc == l_atc:
                        if m_name == l_name:
                            return (l_atc, l_name, index)
                        else:
                            if l_name in m_name:
                                print(
                                    "\n{}, ATC: {}, lname: {}, mname: {}".format(
                                        index, l_atc, repr(l_name), repr(m_name)
                                    )
                                )
    except asyncio.TimeoutError:
        print("timeout error on index: ", index)
    return 0


async def main(n_reqs: int, single):
    timeout = aiohttp.ClientTimeout(total=6 * 60)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        res = await asyncio.gather(
            *[get(session, url, data) for url in urls(n_reqs, single)]
        )

        final_res = [r for r in res if r]
        print(
            "len(final_res):",
            len(final_res),
        )
        print("\nfinal results:")
        print(*final_res, sep="\n")
        write_to_csv(final_res)


def write_to_csv(final_res):
    # read by default 1st sheet of an excel file
    df = pd.read_excel(SRC)
    all_data = df.values.tolist()
    data = [x for x in all_data if x[0] == "X"]
    for i, (_, _, _, d_atc, d_name) in enumerate(data):
        for l_atc, l_name, index in final_res:
            if d_atc == l_atc and d_name == l_name:
                data[i].append(index)
    df = pd.DataFrame(
        data,
        columns=[
            "Priority",
            "Active Substance",
            "Pharmaceutical Form",
            "ATC",
            "Name",
            "Index",
        ],
    )
    df.to_csv(DST)


if __name__ == "__main__":
    data = get_data(SRC)
    print(len(data))
    print(*data[:10], sep="\n")

    n_reqs = 11000
    # n_reqs = 1000
    single = False

    start = perf_counter()
    asyncio.run(main(n_reqs, single))
    end = perf_counter()

    print(f"{n_reqs / (end - start)} req/s")
    print("total time: ", end - start)
