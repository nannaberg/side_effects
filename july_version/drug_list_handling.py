import pandas as pd


SRC = "docs1/All_drugs_DK_all formulations_checked_if_priority_ongoing_130624.xlsx"
# DST = "drugs_with_indices.csv"


def get_all_data():
    # read by default 1st sheet of an excel file
    df = pd.read_excel(SRC)
    return df.values.tolist()


def get_all_data_with_indices():
    df = pd.read_csv("drugs_with_indices.csv", keep_default_na=False)
    values = df.values.tolist()
    return [x[2:] for x in values if x[1] == "X" and x[6]]


def get_all_prioritized_data_with_or_without_indices():
    df = pd.read_csv("drugs_with_indices.csv", keep_default_na=False)
    values = df.values.tolist()
    return [x[2:] for x in values if x[1] == "X"]

def get_all_docs_titles():
    df = pd.read_csv("docs_titles_found.csv", keep_default_na=False)
    values = df.values.tolist()
    return values

def get_data():
    all_data = get_all_data()
    data = [(x[3], x[4]) for x in all_data if x[0] == "X"]
    return data


def get_atc_codes():
    all_data = get_all_data()
    data = [x[3] for x in all_data if x[0] == "X"]
    return list(set(data))


def get_formulations():
    all_data = get_all_data()
    formulations = [x[2] for x in all_data if x[0] == "X"]
    return formulations


def write_to_csv(formulations, cols, dst):
    df = pd.DataFrame(formulations, columns=cols)
    df.to_csv("{}.csv".format(dst))


# atc_codes = get_atc_codes()
# print(len(atc_codes))
# write_to_csv(atc_codes, ["atc_codes"], "atc_codes_list")

# formulations = list(set(get_formulations(SRC)))
# print("\nFormulation:")
# print(*formulations, sep="\n\t")
# print(len(formulations))
# write_to_csv(formulations, ["Formulation"], "formulation_list")
