from bs4 import BeautifulSoup
import requests
import csv


page = requests.get("https://utilities.registrar.indiana.edu/course-browser/browser/research/soc4248fac.html")
soup = BeautifulSoup(page.text, "html.parser")

classTitle = soup.find_all("b")


data = [["course_id","title","credits","department","level"]]
for ct in classTitle:
    if ct.text.find(" CR)") != -1:
        idn = ct.text.index(" ")+1
        while ct.text[idn] != " ":
            idn += 1
        id = ct.text[0:idn]
        cn = ct.text.index(" CR)")-1
        while ct.text[cn] != "(":
            cn -= 1
        cred = ct.text[cn+1:ct.text.index(" CR)")]
        dep = ct.text[0:ct.text.index("-")]
        level = id[idn-3:idn-2]+"00"
        title = ct.text[idn+1:cn-1]
        if title[0] == '"':
            title = title[1:len(title)-1]
        title = title[1:len(title)-1]
        data.append([id,title,cred,dep,level])

with open("data.csv", 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerows(data)