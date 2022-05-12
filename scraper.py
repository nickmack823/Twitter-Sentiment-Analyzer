import time
import json

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select

chrome_driver_path = "C:\Development\chromedriver.exe"
service = Service(chrome_driver_path)
driver = webdriver.Chrome(service=service)

# TWITTER CRAWL DELAY: 1 SECOND

search_url = 'https://twitter.com/search-advanced'
with open('locations.json') as f:
    locations = json.load(f)
    xpaths = locations['xpaths']


def search(keyword, start_date, end_date):
    start_month, start_day, start_year = start_date
    end_month, end_day, end_year = end_date
    driver.get(search_url)
    time.sleep(3)

    # Keyword input
    exact_phrase_bar = driver.find_element(by=By.NAME, value='thisExactPhrase')
    exact_phrase_bar.click()
    exact_phrase_bar.send_keys(keyword)

    scroll = driver.find_element(by=By.XPATH, value=xpaths['scroll'])
    driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scroll)

    # Start month, day, year
    from_month = Select(driver.find_element(by=By.XPATH, value=xpaths['from_month']))
    from_month_options = from_month.options

    for o in from_month_options:
        if o.text == start_month:
            from_month.select_by_index(from_month_options.index(o))
            break
    from_day = Select(driver.find_element(by=By.XPATH, value=xpaths['from_day']))
    from_day_options = from_day.options

    for o in from_day_options:
        if o.text == start_day:
            from_day.select_by_index(from_day_options.index(o))
            break

    from_year = Select(driver.find_element(by=By.XPATH, value=xpaths['from_year']))
    from_year_options = from_year.options
    for o in from_year_options:
        if o.text == start_year:
            from_year.select_by_index(from_year_options.index(o))
            break

    # End month, day, year
    to_month = Select(driver.find_element(by=By.XPATH, value=xpaths['to_month']))
    to_month_options = to_month.options

    for o in to_month_options:
        if o.text == end_month:
            to_month.select_by_index(to_month_options.index(o))
            break
    to_day = Select(driver.find_element(by=By.XPATH, value=xpaths['to_day']))
    to_day_options = to_day.options

    for o in to_day_options:
        if o.text == end_day:
            to_day.select_by_index(to_day_options.index(o))
            break

    to_year = Select(driver.find_element(by=By.XPATH, value=xpaths['to_year']))
    to_year_options = to_year.options
    for o in to_year_options:
        if o.text == end_year:
            to_year.select_by_index(to_year_options.index(o))
            break

    # Parameters set, now search
    search_button = driver.find_element(by=By.XPATH, value=xpaths['search_button'])
    search_button.click()



start = ('January', '6', '2014')
end = ('October', '2', '2016')
search('test', start, end)

