# importing pandas module
import pandas as pd
import sys


def convert_to_number(value):
    try:
        # Try to convert the value to a float (if possible)
        return int(value)
    except ValueError:
        # If conversion fails, return the value as is (treat it as text)
        return value


def convert_to_date(value):
    try:
        # Try to convert the value to a date
        return pd.to_datetime(value, errors="raise").date()
    except ValueError:
        # If conversion fails, return the value as is (keep it as a string)
        return value


n = len(sys.argv)
if n <= 1:
    print("no argument was given")
else:
    csv_to_convert = sys.argv[1]
    # print(csv_to_convert)
    if not csv_to_convert.endswith(".csv"):
        print("argument should be a .csv file")
    else:
        # reading the csv file
        df = pd.read_csv(csv_to_convert)
        df["Index"] = df["Index"].apply(convert_to_number)
        df["Revision date"] = df["Revision date"].apply(convert_to_date)
        # creating an output excel file
        ex_name = csv_to_convert[:-4] + ".xlsx"

        with pd.ExcelWriter(
            ex_name,
            engine="xlsxwriter",
        ) as writer:
            df.to_excel(writer, index=False)
            workbook = writer.book
            worksheet = writer.sheets["Sheet1"]
            header_format = workbook.add_format(
                {"bold": True, "border": False, "text_wrap": True}
            )

            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)

            twrap = workbook.add_format({"text_wrap": True})

            width_dict = {
                "Dosage": 60,
                "Registered indication": 60,
                "Contraindications": 60,
                "Warnings and precautions": 60,
                "Dosereduction liver": 60,
                "Halftime": 60,
                "eGFR": 60,
                "Active substance": 50,
                "Pharmaceutical form": 50,
                "Revision date": 15,
            }

            for k, v in width_dict.items():
                idx_location = df.columns.get_loc(k)
                worksheet.set_column(idx_location, idx_location, v, twrap)
           
            print("all OK!")
