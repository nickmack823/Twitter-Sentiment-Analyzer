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

with open("locations.json") as f:
    locations = json.load(f)
    xpaths = locations['xpaths']
    classes = locations['classes']


def search(hashtag, start_date, end_date):
    """
    Accesses results page from advanced Twitter search with given search parameters, accessing tweets
    that contain the hashtag to search within the given timeframe.
    :param hashtag:
    :param start_date:
    :param end_date:
    :return:
    """
    start_month, start_day, start_year = start_date
    end_month, end_day, end_year = end_date
    driver.get(search_url)

    # Keyword input (Use WebDriverWait to wait until the element is loaded)
    exact_phrase_bar = WebDriverWait(driver, 20).until \
        (expected_conditions.presence_of_element_located((By.NAME, 'theseHashtags')))
    exact_phrase_bar.click()
    exact_phrase_bar.send_keys(hashtag)

    scroll = driver.find_element(by=By.XPATH, value=xpaths['scroll'])
    driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scroll)

    min_likes = driver.find_element(by=By.NAME, value='minLikes')
    min_likes.send_keys('100')

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
    text_data, date_data, likes_data, retweets_data = [], [], [], []
    collected_tweets = []
    page_height = driver.execute_script("return document.body.scrollHeight")
    total_scrolled_height = 0
    results_ended = False
    # While the number to scrape has not been met and there are still results available, scrape tweets
    while len(text_data) < num_tweets_to_scrape and total_scrolled_height < page_height:
        # Get HTML elements of currently loaded tweets
        tweets = WebDriverWait(driver, 20).until \
            (expected_conditions.presence_of_all_elements_located((By.CSS_SELECTOR, "[data-testid='tweet']")))

        texts, dates, likes, retweets = [], [], [], []
        # Scrape currently available tweets
        for t in tweets:
            try:
                # Scroll to tweet to ensure all of its elements are loaded, avoiding visited tweets
                if t not in collected_tweets:
                    loc = t.location
                    driver.execute_script(f"window.scrollTo({loc['x']}, {loc['y']})")
                    collected_tweets.append(t)
                    tweet_text = t.find_element(By.CSS_SELECTOR, "[data-testid='tweetText']").text
                    # Skip duplicated tweets (i.e. spambots)
                    if tweet_text not in texts:
                        texts.append(t.find_element(By.CSS_SELECTOR, "[data-testid='tweetText']").text)
                        dates.append(t.find_element(By.CLASS_NAME, classes['dates']).text)
                        likes.append(t.find_element(By.CSS_SELECTOR, "[data-testid='like']").text)
                        retweets.append(t.find_element(By.CSS_SELECTOR, "[data-testid='retweet']").text)
                    else:
                        print('skipping duplicate tweet')
            except exceptions.StaleElementReferenceException:
                pass

        # If no new data was scraped during this loop iteration, break, no more scraping to be done.
        if len(texts) == 0:
            results_ended = True
            break
        # Update main data lists
        text_data.extend(texts)
        date_data.extend(dates)
        likes_data.extend(likes)
        retweets_data.extend(retweets)

        # Get new page height and scrolled height, waiting for 1 second to account for page loading when scrolling
        time.sleep(1)
        page_height = driver.execute_script("return document.body.scrollHeight")
        total_scrolled_height = driver.execute_script("return window.pageYOffset + window.innerHeight")
        if total_scrolled_height >= page_height:
            results_ended = True

    if len(text_data) >= num_tweets_to_scrape:
        print(f"{len(text_data)} tweets scraped.")
    elif results_ended:
        print(f'End of results, scraped {len(text_data)} tweets.')
    else:
        print("Scraping failed.")

    # End driver and return scraped data
    # driver.quit()
    return text_data, date_data, likes_data, retweets_data


def clean_data(data):
    """
    Iterates through data lists and clean them.
    :param data: a tuple of lists
    :return: the input tuple with cleaned list elements
    """
    for n in range(len(data[0])):
        text = data[0][n]
        likes = data[2][n]
        retweets = data[3][n]

        # Remove newline characters from text
        text_index = data[0].index(text)
        data[0][text_index] = text.replace('\n', '')

        # If tweet has no likes (and thus '' as that value), set value to 0. Else, send string value to integer
        likes_index = data[2].index(likes)
        data[2][likes_index] = 0 if likes == '' else int(likes)

        # Same for retweets
        retweets_index = data[3].index(retweets)
        data[3][retweets_index] = 0 if retweets == '' else int(retweets)

    return data


# Write collected tweets to a CSV file
def save_to_csv(cleaned_data):
    months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October',
              'November', 'December']
    start_date = f"{months.index(start[0])+1}-{start[1]}-{start[2]}"
    end_date = f"{months.index(end[0])+1}-{end[1]}-{end[2]}"

    with open(f"{tag}_{start_date}_to_{end_date}.csv", 'w', encoding='utf-8') as f:
        writer = csv.writer(f)
        headers = ['tweet', 'date', 'likes', 'retweets']
        writer.writerow(headers)
        for n in range(len(cleaned_data[0])):
            row = [cleaned_data[0][n], cleaned_data[1][n], cleaned_data[2][n], cleaned_data[3][n]]
            writer.writerow(row)


# Set parameters and search
start = ('January', '1', '2014')
end = ('January', '31', '2014')
tag = 'GunControl'
search(tag, start, end)
tweets_to_scrape = 500

# Scrape tweets
scraped_data = scrape(tweets_to_scrape)

# Clean scraped data
data_cleaned = clean_data(scraped_data)

# Save data to CSV
save_to_csv(data_cleaned)

