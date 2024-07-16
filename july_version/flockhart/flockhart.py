import requests
from bs4 import BeautifulSoup
import os

flockhart_table = "flockhart_table.html"
keepers = ["1A2", "2C9", "2C19", "2D6", "3A4/5"]


def save_flockhart_to_file(soup):
    with open(flockhart_table, "w", encoding="utf-8") as file:
        file.write(str(soup))


def fetch_flockhart_table():
    response = requests.get("https://drug-interactions.medicine.iu.edu/MainTable.aspx")
    status = response.status_code
    if status == 200:
        soup = BeautifulSoup(response.text, "lxml")
        return soup


def load_flockhart_table():
    with open(flockhart_table, "rb") as file:
        soup = BeautifulSoup(file, "lxml")
    return soup


def get_isoform_dict(header):
    header_section = header.parent.parent
    first_td = header_section.find("td")
    all_tds = [first_td] + first_td.find_next_siblings("td")
    condition = lambda td: td.strong.text.strip() in keepers
    filtered_tds = [td for td in all_tds if condition(td)]
    isoform_dict = {}
    for td in filtered_tds:
        isoform = td.strong.text.strip()
        all_buttons = td.find_all("button")
        all_drugs = [btn.text.strip() for btn in all_buttons]
        isoform_dict[isoform] = all_drugs
    return isoform_dict


def get_flockhart_dict(update_local_table=False):
    soup = get_soup(update_local_table)
    headers = soup.find_all("h1")[1:]
    flockhart_dict = {}
    for header in headers:
        flockhart_dict[header.text.strip()] = get_isoform_dict(header)
    return flockhart_dict


def test(flockhart_dict):
    headers = ["Substrates", "Inhibitors", "Inducers"]
    actual_lengths = {
        headers[0]: [31, 36, 42, 66, 170],
        headers[1]: [13, 17, 21, 39, 44],
        headers[2]: [8, 8, 7, 0, 27],
    }
    for header in headers:
        isoform_dict = flockhart_dict[header]
        for i, isoform in enumerate(keepers):
            expected = actual_lengths[header][i]
            actual = len(isoform_dict[isoform])
            assert expected == actual, "Expected: {}, Actual: {}".format(
                expected, actual
            )
    print("All length tests passed")
    expected_values_dict = {
        headers[0]: [
            ["apremilast", "zolmitriptan", "cyclobenzaprine"],
            ["amitriptyline", "zafirlukast", "clopidogrel"],
            ["amitriptyline", "voriconazole", "chloramphenicol"],
            ["alprenolol", "zuclopenthixol", "atomoxetine"],
            ["abemaciclib", "zolpidem", "alfentanil"],
        ],
        headers[1]: [
            ["amiodarone", "vemurafenib", "efavirenz"],
            ["amiodarone", "zafirlukast", "fenofibrate"],
            ["armodafinil", "voriconazole", "esomeprazole"],
            ["abiraterone", "vemurafenib", "chlorpromazine"],
            ["adagrasib", "voriconazole", "boceprevir"],
        ],
        headers[2]: [
            ["beta-naphthoflavone", "tobacco", "omeprazole"],
            ["carbamazepine", "st. john's wort", "phenobarbital"],
            ["efavirenz", "st. john's wort", "rifampin"],
            [None, None, None],
            ["betamethasone", "vemurafenib", "dabrafenib"],
        ],
    }
    for header in headers:
        isoform_dict = flockhart_dict[header]
        for i, isoform in enumerate(keepers):
            expected_values = expected_values_dict[header][i]
            drugs = isoform_dict[isoform]
            for j1, j2 in enumerate([0, len(drugs) - 1, 4]):
                if len(drugs) > abs(j2):
                    actual = drugs[j2]
                else:
                    actual = None
                expected = expected_values[j1]
                assert (
                    expected == actual
                ), "{}, {}, {}: Expected: {}, Actual: {}".format(
                    header, isoform, j2, expected, actual
                )
    print("All value tests passed")
    # checking for weird chars
    # for header, isoform_dict in flockhart_dict.items():
    #     for isoform, drugs in isoform_dict.items():
    #         for drug in drugs:
    #             if not drug.isalnum():
    #                 print(drug, repr(drug))


def get_soup(update_local_table):
    if update_local_table or not os.path.exists(flockhart_table):
        print("Now fetching flockhart table from web and saving it locally")
        soup = fetch_flockhart_table()
        save_flockhart_to_file(soup)
        print("Flockhart table now saved locally")
        print("Using flockhart table fetched from web")
        return soup
    else:
        print("Using local flockhart table")
        soup = load_flockhart_table()
        return soup


def get_drug_isoforms(drug, flockhar_dict):
    drug_isoform_dict = {}
    for header in flockhar_dict.keys():
        isoforms = []
        for isoform, drugs in flockhar_dict[header].items():
            if drug in drugs:
                isoforms.append(isoform)
        drug_isoform_dict[header] = isoforms
    return drug_isoform_dict


def main():
    flockhart_dict = get_flockhart_dict()
    test(flockhart_dict)
    testdrug = "erythromycin"
    print("testing for drug:", testdrug)
    drug_isoforms_dict = get_drug_isoforms(testdrug, flockhart_dict)
    for header, isoforms in drug_isoforms_dict.items():
        print(header)
        print(*isoforms, sep="\n")


if __name__ == "__main__":
    main()
