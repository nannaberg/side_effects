from pprint import pprint
import sys


OUT_DIR = "./databases/"


def get_listed_sideeffects(FILE):
    with open(FILE) as f:
        return sorted(
            list(
                set([" ".join(line.split()) for line in f.read().splitlines() if line])
            )
        )


# returns a dict -> key is the listed_se and value is the mediciament_se that the key does not represent
def get_blacklisted_sideeffects(FILE):
    with open(FILE) as f:
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


def get_lse_superstring(lse, substrings):
    for sub, super in substrings:
        if lse.lower() == sub.lower():
            return super


f1 = "./sideeffect_lists/eps.txt"
f2 = "blacklisted_sideeffects.txt"
# print(get_listed_sideeffects(f1))
# print(get_blacklisted_sideeffects(f2))
# print(get_out_csv_file_name(f1))

# var = [("Dyskinesier", "Tardive dyskinesier"), ("Dystoni", "Akut dystoni")]
# print(get_lse_superstring("Dystoni", var))
# print(get_lse_superstring("Akut dystoni", var))
# if get_lse_superstring("Akut dystoni", var):
#     print("somethings wrong")
# if get_lse_superstring("Dystoni", var):
#     print("correct")
