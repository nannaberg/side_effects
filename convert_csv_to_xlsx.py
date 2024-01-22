# importing pandas module
import pandas as pd

# reading the csv file
cvs1 = pd.read_csv("database.csv")
csv2 = pd.read_csv("database_with_urls.csv")

# creating an output excel file
ex1 = pd.ExcelWriter("auto_database.xlsx")
ex2 = pd.ExcelWriter("auto_database_with_urls.xlsx")

# converting the csv file to an excel file
cvs1.to_excel(ex1, index=False)
csv2.to_excel(ex2, index=False)

# saving the excel file
ex1.close()
ex2.close()
