# importing pandas module
import pandas as pd
import sys


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

            text_cols = [
                "Dosage",
                "Registered indication",
                "Contraindications",
                "Warnings and precautions",
                "Dosereduction liver",
                "Halftime",
                "eGFR",
            ]

            for c in text_cols:
                idx_location = df.columns.get_loc(c)
                worksheet.set_column(idx_location, idx_location, 60, twrap)

            other_cols = ["Active substance", "Revision date", "Pharmaceutical form"]

            for c in other_cols:
                idx_location = df.columns.get_loc(c)
                worksheet.set_column(idx_location, idx_location, 30, twrap)
            print("all OK!")

            # worksheet.set_row(0, 30, twrap)
