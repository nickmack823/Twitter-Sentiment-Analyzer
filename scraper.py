import time
import json
import csv
import pandas
from os.path import exists

from selenium import webdriver
from selenium.common import exceptions
from selenium.common.exceptions import TimeoutException
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

    # min_likes = driver.find_element(by=By.NAME, value='minLikes')
    # min_likes.send_keys('100')

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


def reached_end_of_results(waited=False):
    page_height = driver.execute_script("return document.body.scrollHeight")
    total_scrolled_height = driver.execute_script("return window.pageYOffset + window.innerHeight")
    # Check if scrolled to end of page
    if total_scrolled_height >= page_height:
        # Wait for 5 seconds to allow page to load if there is more content
        if not waited:
            time.sleep(5)
            reached_end_of_results(True)
        else:
            return True


def scrape():
    """
    Scrapes available tweets until parameter limit has been met.
    :return:
    """
    text_data, date_data, likes_data, retweets_data = [], [], [], []
    collected_tweets = []
    page_height = driver.execute_script("return document.body.scrollHeight")
    total_scrolled_height = 0
    results_ended = False
    # While the number to scrape has not been met and there are still results available, scrape tweets
    while total_scrolled_height < page_height:
        # Get HTML elements of currently loaded tweets
        try:
            tweets = WebDriverWait(driver, 10).until \
                (expected_conditions.presence_of_all_elements_located((By.CSS_SELECTOR, "[data-testid='tweet']")))
        except TimeoutException:
            break

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

        # Get new page height and scrolled height
        results_ended = reached_end_of_results()

    # if len(text_data) >= num_tweets_to_scrape:
    #     print(f"{len(text_data)} tweets scraped from.")
    if results_ended:
        print(f'End of results, scraped {len(text_data)} tweets.')
    else:
        print("Scraping failed.")

    # End driver and return scraped data
    # driver.quit()
    return text_data, date_data, likes_data, retweets_data


def clean_data(data):
    """
    Iterates through input tuple of data lists and cleans them.
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
        data[2][likes_index] = 0 if likes == '' else int(likes.replace(',', ''))

        # Same for retweets
        retweets_index = data[3].index(retweets)
        data[3][retweets_index] = 0 if retweets == '' else int(retweets.replace(',', ''))

    return data


# Write collected tweets to a CSV file
def save_to_csv(cleaned_data):
    """
    Saves cleaned data to an existing CSV file if one exists, else writes to a new file.
    :param cleaned_data:
    :return:
    """
    file_name = f"{tag}.csv"
    # Check if file exists already
    file_exists = exists(file_name)
    # If it exists, append data to existing file
    if file_exists:
        # Get existing rows to prevent adding duplicate data
        with open(file_name, 'r', encoding='utf-8') as file1:
            existing_rows_text = {line[0] for line in csv.reader(file1, delimiter=',')} # Set -t < list -t for lookup

            # Write to existing file
            with open(file_name, 'a', encoding='utf-8', newline='') as file2:
                writer = csv.writer(file2)
                duplicates = 0
                for n in range(len(cleaned_data[0])):
                    row = [cleaned_data[0][n], cleaned_data[1][n], cleaned_data[2][n], cleaned_data[3][n]]
                    if row[0] not in existing_rows_text:
                        writer.writerow(row)
                    else:
                        duplicates += 1
                print(f'Skipped {duplicates} duplicate rows.')
    else:
        # Write to new CSV (newline set to '' to prevent empty rows between each entry)
        with open(file_name, 'w', encoding='utf-8', newline='') as file3:
            writer = csv.writer(file3)
            # If writing to new file, add header row
            headers = ['tweet', 'date', 'likes', 'retweets']
            writer.writerow(headers)
            for n in range(len(cleaned_data[0])):
                row = [cleaned_data[0][n], cleaned_data[1][n], cleaned_data[2][n], cleaned_data[3][n]]
                writer.writerow(row)


def collect_top_tweets_month(month, year):
    months_with_31_days = ['January', 'March', 'May', 'July', 'August', 'October', 'December']

    # Determine final day of the given month
    if month == 'February':
        # Check for leap year
        y = int(year)
        if ((y % 400 == 0) and (y % 100 == 0)) or ((y % 4 == 0) and (y % 100 != 0)):
            final_day = '29'
            print('LEAP YEAR')
        else:
            final_day = '28'
            print('NOT LEAP YEAR')
    else:
        final_day = '31' if month in months_with_31_days else '30'

    days = [str(day) for day in range(1, int(final_day)+1)]
    print(days)

    # Start collecting tweets from each day
    for day in days:
        if day == final_day:
            break
        start = (month, day, year)
        end = (month, days[days.index(day)+1], year)
        print(f'Scraping from {start} to {end}')
        search(tag, start, end)

        # Scrape tweets
        scraped_data = scrape()
        print(f'Scraped data from {start} to {end}')

        # Clean scraped data
        data_cleaned = clean_data(scraped_data)

        # Save data to CSV
        save_to_csv(data_cleaned)


def collect_top_tweets_day(day, month, year):
    start = (month, day, year)
    print(f'Scraping from {start} to {start}')
    search(tag, start, start)

    # Scrape tweets
    scraped_data = scrape()
    print(f'Scraped data from {start} to {start}')

    # Clean scraped data
    data_cleaned = clean_data(scraped_data)

    # Save data to CSV
    save_to_csv(data_cleaned)


# Set parameters and search
tag = 'abortion'
# tweets_to_scrape = 500
# collect_top_tweets_month('February', '2020')
collect_top_tweets_day(1, 'February', '2022')