import pandas as pd
from bs4 import BeautifulSoup
import asyncio
import aiohttp
from time import perf_counter

SRC = "Priority_drugs_Name_ATC_Formulation_02_10_24.xlsx"
DST = "final_drugs_with_indices.csv"


def get_data(file):
    # read by default 1st sheet of an excel file
    df = pd.read_excel(file)
    data = df.values.tolist()
    # data = [(x[3], x[4], x[2]) for x in all_data if x[0] == "X"]
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
    # num_index = next((i for i, c in enumerate(title) if c.isdigit()), len(title))
    # if num_index:
    #     title = title[:num_index].strip()
    return title


def get_active_substances(soup, atc, index):
    active_substances = []
    parent = soup.find(attrs={"class": "SpaceBtm IndholdsstofferHeaderLinks"})
    if parent == None:
        noparent = soup.find(
            title="Lægemidlet kan være helt udgået eller midlertidigt udgået pga. leveringssvigt"
        )
        print("In get_generic_name: Parent was none, index: ", index)
        # print(noparent.text)
        # return noparent.text
        active_substances.append("na")
        return active_substances
    children = parent.find_all("b")

    for b in children:
        active_substances.append(b.text)
    return active_substances


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
                if int(index) % 100 == 0:
                    print(index, status, length)
                if m_atc:
                    m_name = get_name(soup)
                    m_substance = get_active_substances(soup, m_atc, index)

                # to get list of names to figure out how to get indices
                # first check for all listed drugs if the current m_drug matches atc and name perfectly
                # for l_atc, l_name, l_formulation in data:
                #     if m_atc == l_atc:
                #         if l_name == m_name:
                #             return (
                #                 index,
                #                 m_atc,
                #                 m_name,
                #                 l_name,
                #                 l_formulation,
                #                 "perfect match",
                #             )
                # then if not, check for all listed drugs if for matching atc's the current m_drug contains the l_name
                # for l_atc, l_name, l_formulation in data:
                #     if m_atc == l_atc:
                #         if l_name in m_name:
                #             return (index, m_atc, m_name, l_name, l_formulation, "")
                for l_substance, l_atc in data:
                    if l_atc == m_atc:
                        return (l_substance, m_substance, l_atc, m_name, index)
                # for l_atc, l_name, l_formulation in data:
                #     if m_atc == l_atc:
                #         if m_name == l_name:
                #             return (l_atc, l_name, index)
                #         else:
                #             if l_name in m_name and l_formulation in m_name:
                #                 return (l_atc, l_name, index)
                #             elif l_name in m_name:
                #                 print(
                #                     "\n{}, ATC: {}, lname: {}, mname: {}".format(
                #                         index, l_atc, repr(l_name), repr(m_name)
                #                     )
                #                 )
    except asyncio.TimeoutError:
        print("timeout error on index: ", index)
    return 0


async def main(n_reqs: int, single, data):
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
        # print("\nfinal results:")
        # print(*final_res, sep="\n")
        write_to_csv(data, final_res)
        # write_names_to_csv(final_res)


# def write_names_to_csv(final_res):
#     df = pd.DataFrame(
#         final_res,
#         columns=["index", "atc", "m_name", "l_name", "l_formulations", "match type"],
#     )
#     df.to_csv("drug_list_original_names.csv")


def write_to_csv(data, final_res):

    # read by default 1st sheet of an excel file
    df = pd.read_excel(SRC)
    new_data = []
    # all_data = df.values.tolist()
    # data = [x for x in all_data if x[0] == "X"]
    for i, (d_substance, d_atc) in enumerate(data):
        match = False
        for l_substance, m_substance, l_atc, m_name, index in final_res:
            if d_atc == l_atc:
                match = True

                new_d = [l_substance, ", ".join(m_substance), l_atc, m_name, index]
                # new_d.append(m_name)
                # new_d.append(index)
                new_data.append(new_d)
                # data[i].append(m_name)
                # data[i].append(index)
                # print(data[i])
            # else:
            #     new_d.append("na")
            #     new_d.append("na")
            # new_data.append(new_d)
        if not match:
            new_d = [d_substance, "na", d_atc, "na", "na"]
            new_data.append(new_d)
    df = pd.DataFrame(
        new_data,
        columns=[
            "l_Active Substance",
            "m_Active Substance",
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

    n_reqs = 12000
    n_reqs = 4291
    single = True

    start = perf_counter()
    asyncio.run(main(n_reqs, single, data))
    end = perf_counter()

    print(f"{n_reqs / (end - start)} req/s")
    print("total time: ", end - start)
