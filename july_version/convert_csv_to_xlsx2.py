# importing pandas module
import pandas as pd
import sys


n = len(sys.argv)
# print(n)
if n <= 1:
    print("no argument was given")
else:
    csv_to_convert = sys.argv[1]
    # print(csv_to_convert)
    if not csv_to_convert.endswith(".csv"):
        print("argument should be a .csv file")
    else:
        # # reading the csv file
        df = pd.read_csv(csv_to_convert)
        # # creating an output excel file
        ex_name = csv_to_convert[:-4] + ".xlsx"
        # print(ex_name)
        # ex = pd.ExcelWriter(ex_name)
        # # converting the csv file to an excel file
        # csv.to_excel(ex, index=False)

        # # saving the excel file
        # ex.close()
        renal_info_col = "renal_info"
        renal_info_col = "registered indication"
        print(repr(df[renal_info_col]))
        # for row in df[renal_info_col]:
        #     print("row: ", row)
        # df[renal_info_col] = df[renal_info_col].str.join("\n")
        # print(repr(df[renal_info_col]))

        with pd.ExcelWriter(
            ex_name,
            engine="xlsxwriter",
        ) as writer:
            df.to_excel(writer, index=False)
            # print(repr(df["renal_info"]))
            workbook = writer.book
            worksheet = writer.sheets["Sheet1"]
            header_format = workbook.add_format(
                {"bold": True, "border": False, "text_wrap": True}
            )

            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)

            twrap = workbook.add_format({"text_wrap": True})
            idx_location = df.columns.get_loc(renal_info_col)
            worksheet.set_column(idx_location, idx_location, 60, twrap)

            # worksheet.set_row(0, 30, twrap)
