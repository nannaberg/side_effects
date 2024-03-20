# importing pandas module
import pandas as pd
import sys


n = len(sys.argv)
print(n)
if n == 0:
    print("no argument was given")
else:
    csv_to_convert = sys.argv[1]
    print(csv_to_convert)
    if not csv_to_convert.endswith(".csv"):
        print("argument should be a .csv file")
    else:
        # reading the csv file
        csv = pd.read_csv(csv_to_convert)
        # creating an output excel file
        ex_name = csv_to_convert[:-4] + ".xlsx"
        print(ex_name)
        ex = pd.ExcelWriter(ex_name)
        # converting the csv file to an excel file
        csv.to_excel(ex, index=False)

        # saving the excel file
        ex.close()
