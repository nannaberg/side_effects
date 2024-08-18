# import requests
from bs4 import BeautifulSoup
from requests_html import HTMLSession

session = HTMLSession()

response = session.get("https://go.drugbank.com/atc/G03BA03")

response.html.render(sleep=2)

# response = requests.get("https://go.drugbank.com/atc/G03BA03")

status = response.status_code
length = len(response.content)
print(status)
print(length)

atc_code = "G03BA03"
soup = BeautifulSoup(response.html.html, "lxml")
drug = soup.find(id=atc_code)
print(drug.prettify())
# print(soup.prettify())
# text1 = soup.find_all("h1")
# print(text1)
# substrates_header = text1[1]
# gp = substrates_header.parent.parent
# print(gp.button.text)

# print(soup.prettify())
