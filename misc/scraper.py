from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import pyautogui
import time
import csv

options = Options()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
pageD = driver.get("https://sisjee.iu.edu/sisigps-prd/web/igps/course/search/")
button = driver.find_element(By.CLASS_NAME, "rvt-select")
select = Select(button)
select.select_by_visible_text("IU Bloomington")
wait = WebDriverWait(driver, 10)
links = wait.until(EC.presence_of_element_located((By.ID, "cs-term-search__select")))
button2 = driver.find_element(By.ID, "cs-term-search__select")
select2 = Select(button2)
select2.select_by_index(2)

links = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "rvt-button--secondary")))
number = 0
while number < 129:
    links = wait.until(EC.presence_of_element_located((By.XPATH, "//button[text()='Load More']")))
    pyautogui.scroll(-100000)
    driver.find_element(By.XPATH, "//button[text()='Load More']").click()
    number += 1

time.sleep(2)
html = driver.page_source
soup = BeautifulSoup(html, "html.parser")

classTest = soup.find_all("p", class_="rvt-m-all-none")
descTest = soup.find_all("p", class_="rvt-m-bottom-xs rvt-m-top-none")

data = [["course_id","title","credits","department","level","description","terms_offered"]]
numc = 0
numd = 0
while numc < len(classTest):
    temp = classTest[numc].text
    id = temp
    title = classTest[numc+2].text
    cred = classTest[numc+1].text
    department = temp[0:temp.index("-")]
    level = temp[len(temp)-3] + "00"
    term = descTest[numd].text
    if(descTest[numd+1].text[1] == 'l'):
        numd +=1
    desc = descTest[numd+1].text
    data.append([id,title,cred,department,level,desc,term])
    numc+=3
    numd+=2







driverTwo = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
pageDTwo = driverTwo.get("https://sisjee.iu.edu/sisigps-prd/web/igps/course/search/")
buttonTwo = driverTwo.find_element(By.CLASS_NAME, "rvt-select")
selectTwo = Select(buttonTwo)
selectTwo.select_by_visible_text("IU Bloomington")
waitTwo = WebDriverWait(driverTwo, 10)
linksTwo = waitTwo.until(EC.presence_of_element_located((By.ID, "cs-term-search__select")))
button2Two = driverTwo.find_element(By.ID, "cs-term-search__select")
select2Two = Select(button2Two)
select2Two.select_by_index(4)

linksTwo = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "rvt-button--secondary")))
number = 0
while number < 127:
    linksTwo = waitTwo.until(EC.presence_of_element_located((By.XPATH, "//button[text()='Load More']")))
    pyautogui.scroll(-100000)
    driverTwo.find_element(By.XPATH, "//button[text()='Load More']").click()
    number += 1

time.sleep(2)
htmlTwo = driverTwo.page_source
soupTwo = BeautifulSoup(htmlTwo, "html.parser")

classTestTwo = soupTwo.find_all("p", class_="rvt-m-all-none")
descTestTwo = soupTwo.find_all("p", class_="rvt-m-bottom-xs rvt-m-top-none")

numc = 0
numd = 0
while numc < len(classTestTwo):
    if descTestTwo[numd].text.find(": Fall") != -1:
        temp = classTestTwo[numc].text
        id = temp
        title = classTestTwo[numc+2].text
        cred = classTestTwo[numc+1].text
        department = temp[0:temp.index("-")]
        level = temp[len(temp)-3] + "00"
        term = descTestTwo[numd].text
        if(descTestTwo[numd+1].text[1] == 'l'):
            numd +=1
        desc = descTestTwo[numd+1].text
        data.append([id,title,cred,department,level,desc,term])
    if(descTestTwo[numd+1].text[0] == 'T'):
            numd +=1
    numc+=3
    numd+=2







with open("courseDataFS.csv", 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerows(data)