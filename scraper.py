import time
import json
import csv

from selenium import webdriver
from selenium.common import exceptions
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.wait import WebDriverWait

chrome_driver_path = "C:\Development\chromedriver.exe"
service = Service(chrome_driver_path)
driver = webdriver.Chrome(service=service)

# TWITTER CRAWL DELAY: 1 SECOND

search_url = 'https://twitter.com/search-advanced'
text_data, date_data, likes_data, retweets_data = [], [], [], []

with open('locations.json') as f:
    locations = json.load(f)
    xpaths = locations['xpaths']
    classes = locations['classes']


def search(keyword, start_date, end_date):
    start_month, start_day, start_year = start_date
    end_month, end_day, end_year = end_date
    driver.get(search_url)

    # Keyword input (Use WebDriverWait to wait until the element is loaded)
    exact_phrase_bar = WebDriverWait(driver, 20).until \
        (expected_conditions.presence_of_element_located((By.NAME, 'thisExactPhrase')))
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


def scrape(num_tweets_to_scrape):
    """
    Scrapes available tweets until parameter limit has been met.
    :param num_tweets_to_scrape:
    :return:
    """

    while len(text_data) < num_tweets_to_scrape:
        # Get HTML elements of currently loaded tweets
        # texts = WebDriverWait(driver, 20).until \
        #     (expected_conditions.presence_of_all_elements_located((By.CSS_SELECTOR, "[data-testid='tweetText']")))
        # dates = WebDriverWait(driver, 20).until \
        #     (expected_conditions.presence_of_all_elements_located((By.CLASS_NAME, classes['dates'])))
        # likes = WebDriverWait(driver, 20).until \
        #     (expected_conditions.presence_of_all_elements_located((By.CSS_SELECTOR, "[data-testid='like']")))
        # retweets = WebDriverWait(driver, 20).until \
        #     (expected_conditions.presence_of_all_elements_located((By.CSS_SELECTOR, "[data-testid='retweet']")))

        tweets = WebDriverWait(driver, 20).until \
            (expected_conditions.presence_of_all_elements_located((By.CSS_SELECTOR, "[data-testid='tweet']")))

        texts, dates, likes, retweets = [], [], [], []
        for t in tweets:
            try:
                # Scroll to tweet to ensure all of its elements are loaded
                # TODO: Ensure each tweet is scrolled to only once
                loc = t.location
                driver.execute_script(f"window.scrollTo({loc['x']}, {loc['y']})")
                texts.append(t.find_element(By.CSS_SELECTOR, "[data-testid='tweetText']").text)
                dates.append(t.find_element(By.CLASS_NAME, classes['dates']).text)
                likes.append(t.find_element(By.CSS_SELECTOR, "[data-testid='like']").text)
                retweets.append(t.find_element(By.CSS_SELECTOR, "[data-testid='retweet']").text)
            except exceptions.StaleElementReferenceException as e:
                pass
        lengths = len(texts), len(dates), len(likes), len(retweets)
        # print(lengths)
        # print(texts)
        # print(dates)
        # print(likes)
        # print(retweets)

        # Scrape data from loaded tweets, avoiding duplicates (same account tweeting many times, for example)
        # for n in range(len(texts)):
        #     try:
        #         texts_list.append(texts[n].text)
        #         dates_list.append(dates[n].text)
        #         likes_list.append(likes[n].text)
        #         retweets_list.append(retweets[n].text)
        #     except exceptions.StaleElementReferenceException as e:
        #         pass

        # Update main data lists
        text_data.extend(texts)
        date_data.extend(dates)
        likes_data.extend(likes)
        retweets_data.extend(retweets)

        # Get Y coordinate of last loaded tweet and scroll to it to load next set of tweets
        # last_tweet_y = tweets[-1].location['y']
        # driver.execute_script(f"window.scrollTo(0, {last_tweet_y})")
        # time.sleep(1)

    if len(text_data) >= num_tweets_to_scrape:
        print(f"{len(text_data)} tweets scraped.")
    else:
        print("Scraping failed.")


# Write collected tweets to a CSV file
def save_to_csv():
    months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October',
              'November', 'December']
    start_date = f"{months.index(start[0])+1}-{start[1]}-{start[2]}"
    end_date = f"{months.index(end[0])+1}-{end[1]}-{end[2]}"

    with open(f"{keyword}_{start_date}_to_{end_date}.csv", 'w') as f:
        writer = csv.writer(f)
        headers = ['tweet', 'date', 'likes', 'retweets']
        writer.writerow(headers)
        # for n in range(len())


start = ('January', '6', '2014')
end = ('October', '2', '2016')
keyword = 'einhorn'
search(keyword, start, end)
tweets_to_scrape = 100

scrape(tweets_to_scrape)
print(text_data)
print(date_data)
print(likes_data)
print(retweets_data)

