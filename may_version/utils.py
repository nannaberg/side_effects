from pprint import pprint
import sys


OUT_DIR = "./databases/"


def get_listed_sideeffects(file):
    with open(file) as f:
        return sorted(
            list(
                set([" ".join(line.split()) for line in f.read().splitlines() if line])
            )
        )


# returns a dict -> key is the listed_se and value is the mediciament_se that the key does not represent
def get_blacklisted_sideeffects(file):
    with open(file) as f:
        return [
            (elm[0], elm[1])
            for elm in [line.split(";") for line in f.read().splitlines() if line]
        ]
        # return {
        #     elm[0]: elm[1]
        #     for elm in [line.split(";") for line in f.read().splitlines() if line]
        # }


def get_list_name(src):
    return src.split("/")[-1].split(".")[0]


def get_out_csv_file_name(src):
    return OUT_DIR + get_list_name(src) + "_database.csv"


def get_found_substrings_file_name(src):
    return OUT_DIR + "substrings_found_for_" + get_list_name(src) + ".txt"


def my_pprint(x):
    pprint(x, width=120)


# def check_if_substring(lse, substrings):
#     for sub, _ in substrings:
#         if lse.lower() == sub.lower():
#             return True
#     return False


def get_lse_superstrings(lse, substrings):
    supers = []
    for sub, superstring in substrings:
        if lse.lower() == sub.lower():
            supers.append(superstring)
    return supers


# f1 = "./sideeffect_lists/eps.txt"
# f2 = "blacklisted_sideeffects.txt"
# print(get_listed_sideeffects(f1))
# print(get_blacklisted_sideeffects(f2))
# print(get_out_csv_file_name(f1))

# var = [("Dyskinesier", "Tardive dyskinesier"), ("Dystoni", "Akut dystoni")]
# var2 = [
#     ("Arytmier", "Takyarytmier"),
#     ("Hypotension", "Ortostatisk hypotension"),
#     ("Hypotension", "Symptomatisk hypotension"),
#     ("Takykardi", "Torsades de pointes-takykardi"),
# ]
# print(get_lse_superstrings("Dystoni", var))
# print(get_lse_superstrings("Akut dystoni", var))
# if get_lse_superstrings("Akut dystoni", var):
#     print("somethings wrong")
# if get_lse_superstrings("Dystoni", var):
#     print("correct")
# print(get_lse_superstrings("Hypotension", var2))


# inc = True
# lse_superstrings = get_lse_superstrings("Dystoni", var2)
# for lse_super in lse_superstrings:
#     print("somethings is wrong")
#     if lse_super in "Symptomatisk hypotension":
#         inc = False
# print(inc)
# lse_superstrings = get_lse_superstrings("Hypotension", var2)
# for lse_super in lse_superstrings:
#     if lse_super in "Symptomatisk hypotension":
#         inc = False
# print(inc)


def get_substrings(lses1, lses2):
    substrings = []
    for lse1 in lses1:
        for lse2 in lses2:
            if lse1.lower() != lse2.lower() and lse1.lower() in lse2.lower():
                substrings.append((lse1, lse2))
    return substrings


def get_lse_list_path(filename):
    return "sideeffect_lists/" + filename + ".txt"


def get_problematic_substrings():
    bivirkninger_maj = "bivirkninger_maj"
    all_lses = get_listed_sideeffects(get_lse_list_path(bivirkninger_maj))
    # all_substrings = get_substrings(all_lses, all_lses)

    anticholinerge = "anticholinerge"
    eps = "eps"
    kardiologiske = "kardiologiske"
    malignt_neuroleptikasyndrom = "malignt_neuroleptikasyndrom"
    metaboliske = "metaboliske"
    sedation = "sedation"
    serotonergt_syndrom = "serotonergt_syndrom"
    søvn = "søvn"

    filenames = [
        anticholinerge,
        eps,
        kardiologiske,
        malignt_neuroleptikasyndrom,
        metaboliske,
        sedation,
        serotonergt_syndrom,
        søvn,
    ]
    for filename in filenames:
        lses = get_listed_sideeffects(get_lse_list_path(filename))
        only_lse_substrings = get_substrings(lses, lses)
        mixed_substrings = get_substrings(lses, all_lses)
        temp = []
        for elm in mixed_substrings:
            if elm not in only_lse_substrings:
                temp.append(elm)
        print("\n Problematic substrings for {}:".format(filename))
        my_pprint(temp)


# get_problematic_substrings()
