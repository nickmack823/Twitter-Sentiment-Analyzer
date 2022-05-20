import sys
import time
import json
import csv
import pycld2
from os.path import exists
from pathlib import Path
from selenium import webdriver
from selenium.common import exceptions
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.wait import WebDriverWait

# File paths
root_path = Path('.')
scraper_dir = 'scraper_files'
chromedriver_path = root_path / scraper_dir / 'chromedriver.exe'
html_locations_path = root_path / scraper_dir / 'locations.json'

if not exists(html_locations_path):
    sys.exit('Locations JSON file missing, unable to continue.')

f = open(html_locations_path, 'r')
locations = json.load(f)
xpaths = locations['xpaths']
classes = locations['classes']
f.close()


def clean_data(input_data):
    """
    Iterates through input tuple of data lists and cleans them.
    :param input_data: a tuple of lists
    :return: the input tuple with cleaned list elements
    """
    texts_list, dates_list, likes_list, retweets_list = input_data[0], input_data[1], input_data[2], input_data[3]
    output_data = ([], [], [], [])
    non_english_removed, duplicates_removed = 0, 0

    for n in range(len(input_data[0])):
        text = texts_list[n]
        date = dates_list[n]
        likes = likes_list[n]
        retweets = retweets_list[n]
        omit_tweet = False

        # Detect and omit non-English tweets
        lang_data = pycld2.detect(text)[2]
        for lang_tuple in lang_data:
            if lang_tuple[0] != 'ENGLISH' and lang_tuple[0] != 'Unknown':
                non_english_removed += 1
                omit_tweet = True

        # Skip duplicates
        if text in output_data[0]:
            print('DUPLICATE')
            print(text)
            duplicates_removed += 1
            omit_tweet = True

        # If remove, don't add to output data
        if omit_tweet:
            continue
        # print(date)

        new_text = text.replace('\n', '')
        new_date = date

        # If tweet has no likes/retweets (and thus '' as that value), set value to 0. Else, send string value to
        # integer
        new_likes = 0 if likes == '' else int(likes.replace(',', ''))
        new_retweets = 0 if retweets == '' else int(retweets.replace(',', ''))

        output_data[0].append(new_text)
        output_data[1].append(new_date)
        output_data[2].append(new_likes)
        output_data[3].append(new_retweets)

    print(
        f'Data cleaned: {non_english_removed} non-English tweets removed, {duplicates_removed} duplicates removed,'
        f' remaining tweets normalized.')
    return output_data


def save_to_csv(file_name, cleaned_data):
    """
    Saves cleaned data to an existing CSV file if one exists, else writes to a new file.
    :param file_name:
    :param cleaned_data:
    :return:
    """
    # Check if file exists already
    file_path = root_path / scraper_dir / f"{file_name}.csv"
    file_exists = exists(file_path)
    # If it exists, append data to existing file
    if file_exists:
        # Get existing rows to prevent adding duplicate data
        with open(file_path, 'r', encoding='utf-8') as file1:
            existing_rows_text = {line[0] for line in
                                  csv.reader(file1, delimiter=',')}  # Set -t < list -t for lookup

            # Write to existing file
            with open(file_path, 'a', encoding='utf-8', newline='') as file2:
                writer = csv.writer(file2)
                duplicates = 0
                for n in range(len(cleaned_data[0])):
                    tweet, date, likes, retweets = cleaned_data[0][n], cleaned_data[1][n], cleaned_data[2][n], \
                                                   cleaned_data[3][n]
                    row = [tweet, date, likes, retweets]
                    if tweet not in existing_rows_text:
                        writer.writerow(row)
                    else:
                        duplicates += 1
                print(f'Skipped {duplicates} duplicate rows.')
    else:
        # Write to new CSV (newline set to '' to prevent empty rows between each entry)
        with open(file_path, 'w', encoding='utf-8', newline='') as file3:
            writer = csv.writer(file3)
            # If writing to new file, add header row
            headers = ['tweet', 'date', 'likes', 'retweets']
            writer.writerow(headers)
            for n in range(len(cleaned_data[0])):
                tweet, date, likes, retweets = cleaned_data[0][n], cleaned_data[1][n], cleaned_data[2][n], \
                                               cleaned_data[3][n]
                row = [tweet, date, likes, retweets]
                writer.writerow(row)


def get_days_in_month(month, year):
    months_with_31_days = ['January', 'March', 'May', 'July', 'August', 'October', 'December']

    # Determine final day of the given month
    if month == 'February':
        # Check for leap year
        y = int(year)
        if ((y % 400 == 0) and (y % 100 == 0)) or ((y % 4 == 0) and (y % 100 != 0)):
            days = [str(day) for day in range(1, 30)]
        else:
            days = [str(day) for day in range(1, 29)]
    else:
        days = [str(day) for day in range(1, 32)] if month in months_with_31_days else [str(day) for day in
                                                                                        range(1, 31)]

    return days


class Scraper:
    service = Service(str(chromedriver_path))
    driver = webdriver.Chrome(service=service)

    # TWITTER CRAWL DELAY: 1 SECOND

    search_url = 'https://twitter.com/search-advanced'

    # Search params
    word_params, account_params, engagement_params = tuple(), tuple(), tuple()

    date_range = tuple()

    # HTML element info
    xpaths, classes = [], []

    def __init__(self, search_parameters, date_range):
        self.word_params, self.account_params, self.engagement_params = search_parameters
        self.date_range = date_range

    def begin_scraping_process(self, start, end):
        self.collect_top_tweets_in_range(start, end)

    def input_word_parameters(self, parameters):
        all_these_words, exact_phrase, any_these_words, none_these_words, hashtags = parameters

        all_of_these_words = WebDriverWait(self.driver, 20).until \
            (expected_conditions.presence_of_element_located((By.NAME, 'allOfTheseWords')))
        all_of_these_words.send_keys(all_these_words)

        this_exact_phrase = WebDriverWait(self.driver, 20).until \
            (expected_conditions.presence_of_element_located((By.NAME, 'thisExactPhrase')))
        this_exact_phrase.send_keys(exact_phrase)

        any_of_these_words = WebDriverWait(self.driver, 20).until \
            (expected_conditions.presence_of_element_located((By.NAME, 'anyOfTheseWords')))
        any_of_these_words.send_keys(any_these_words)

        none_of_these_words = WebDriverWait(self.driver, 20).until \
            (expected_conditions.presence_of_element_located((By.NAME, 'noneOfTheseWords')))
        none_of_these_words.send_keys(none_these_words)

        # Keyword input (Use WebDriverWait to wait until the element is loaded)
        these_hashtags = WebDriverWait(self.driver, 20).until \
            (expected_conditions.presence_of_element_located((By.NAME, 'theseHashtags')))
        these_hashtags.send_keys(hashtags)

    def input_account_parameters(self, parameters):
        from_accounts, to_accounts, mentioning_accounts = parameters

        from_these_accounts = WebDriverWait(self.driver, 20).until \
            (expected_conditions.presence_of_element_located((By.NAME, 'fromTheseAccounts')))
        from_these_accounts.send_keys(from_accounts)

        to_these_accounts = WebDriverWait(self.driver, 20).until \
            (expected_conditions.presence_of_element_located((By.NAME, 'toTheseAccounts')))
        to_these_accounts.send_keys(to_accounts)

        mentioning_these_accounts = WebDriverWait(self.driver, 20).until \
            (expected_conditions.presence_of_element_located((By.NAME, 'mentioningTheseAccounts')))
        mentioning_these_accounts.send_keys(mentioning_accounts)

    def input_engagement_parameters(self, parameters):
        min_replies, min_likes, min_retweets = parameters

        min_replies_input = self.driver.find_element(by=By.NAME, value='minReplies')
        min_replies_input.send_keys(min_replies)

        min_likes_input = self.driver.find_element(by=By.NAME, value='minLikes')
        min_likes_input.send_keys(min_likes)

        min_retweets_input = self.driver.find_element(by=By.NAME, value='minRetweets')
        min_retweets_input.send_keys(min_retweets)

    def search(self, start_date, end_date):
        """
        Accesses results page from advanced Twitter search with given search parameters, accessing tweets
        that contain the hashtag to search within the given timeframe.
        :param start_date:
        :param end_date:
        :return:
        """
        start_day, start_month, start_year = start_date
        end_day, end_month, end_year = end_date
        self.driver.get(self.search_url)

        self.input_word_parameters(self.word_params)
        self.input_account_parameters(self.account_params)
        self.input_engagement_parameters(self.engagement_params)

        scroll = self.driver.find_element(by=By.XPATH, value=xpaths['scroll'])
        self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scroll)

        # Start month, day, year
        from_month = Select(self.driver.find_element(by=By.XPATH, value=xpaths['from_month']))
        from_month_options = from_month.options
        for o in from_month_options:
            if o.text == start_month:
                from_month.select_by_index(from_month_options.index(o))
                break

        from_day = Select(self.driver.find_element(by=By.XPATH, value=xpaths['from_day']))
        from_day_options = from_day.options
        for o in from_day_options:
            if o.text == start_day:
                from_day.select_by_index(from_day_options.index(o))
                break

        from_year = Select(self.driver.find_element(by=By.XPATH, value=xpaths['from_year']))
        from_year_options = from_year.options
        for o in from_year_options:
            if o.text == start_year:
                from_year.select_by_index(from_year_options.index(o))
                break

        # End month, day, year
        to_month = Select(self.driver.find_element(by=By.XPATH, value=xpaths['to_month']))
        to_month_options = to_month.options
        for o in to_month_options:
            if o.text == end_month:
                to_month.select_by_index(to_month_options.index(o))
                break

        to_day = Select(self.driver.find_element(by=By.XPATH, value=xpaths['to_day']))
        to_day_options = to_day.options
        for o in to_day_options:
            if o.text == end_day:
                to_day.select_by_index(to_day_options.index(o))
                break

        to_year = Select(self.driver.find_element(by=By.XPATH, value=xpaths['to_year']))
        to_year_options = to_year.options
        for o in to_year_options:
            if o.text == end_year:
                to_year.select_by_index(to_year_options.index(o))
                break

        # Parameters set, now search
        search_button = self.driver.find_element(by=By.XPATH, value=xpaths['search_button'])
        search_button.click()

    def reached_end_of_results(self, waited_for_load=False):
        page_height = self.driver.execute_script("return document.body.scrollHeight")
        total_scrolled_height = self.driver.execute_script("return window.pageYOffset + window.innerHeight")
        # Check if scrolled to end of page
        if total_scrolled_height >= page_height:
            # Wait for 5 seconds to allow page to load if there is more content
            if not waited_for_load:
                # loading = self.driver.execute_script("return document.readyState")
                # print(loading)
                time.sleep(3)
                return self.reached_end_of_results(waited_for_load=True)
            else:
                print('End of results reached')
                return True

    def scrape_displayed_tweet_elements(self, tweet_elements, collected_elements):
        newly_collected = []
        texts, dates, likes, retweets = [], [], [], []
        # Scrape currently available tweets
        for t in tweet_elements:
            try:
                # Scroll to tweet to ensure all of its elements are loaded, avoiding visited tweets
                if t not in collected_elements:
                    # loc = t.location
                    # self.driver.execute_script(f"window.scrollTo({loc['x']}, {loc['y']})")
                    newly_collected.append(t)
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

        loc = tweet_elements[-1].location
        self.driver.execute_script(f"window.scrollTo({loc['x']}, {loc['y']})")

        return texts, dates, likes, retweets, newly_collected

    def scrape(self):
        """
        Scrapes available tweets until parameter limit has been met.
        :return:
        """
        text_data, date_data, likes_data, retweets_data = [], [], [], []
        collected_tweets = []
        # While there are still results available, scrape them
        while True:
            # Get HTML elements of currently loaded tweets
            try:
                tweet_elements = WebDriverWait(self.driver, 10).until \
                    (expected_conditions.presence_of_all_elements_located((By.CSS_SELECTOR, "[data-testid='tweet']")))
            except TimeoutException:
                break

            texts, dates, likes, retweets, newly_collected = self.scrape_displayed_tweet_elements \
                (tweet_elements, collected_tweets)
            collected_tweets.extend(newly_collected)

            # Update main data lists
            text_data.extend(texts)
            date_data.extend(dates)
            likes_data.extend(likes)
            retweets_data.extend(retweets)

            results_ended = self.reached_end_of_results()

            if results_ended:
                print(f'End of results, scraped {len(text_data)} tweets.')
                break

        return text_data, date_data, likes_data, retweets_data

    def collect_top_tweets_in_range(self, start, end):
        print(f'Scraping from {start} to {end}')
        start_day, start_month, start_year = start
        end_day, end_month, end_year = end

        months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September',
                  'October', 'November', 'December']

        current_day, current_month, current_year = start_day, start_month, start_year
        while current_day != end_day or current_month != end_month or current_year != end_year:
            current_date = (current_day, current_month, current_year)
            print(current_date)
            days_in_current_month = get_days_in_month(start_month, start_year)

            # Final day of month reached, go to next month
            if days_in_current_month[-1] == current_day:
                if current_month == 'December':
                    other_year = str(int(current_year + 1))
                    other_month = 'January'
                else:
                    other_month = months[months.index(current_month) + 1]
                    other_year = current_year
                next_day = '1'
            # Not final month day, go to next
            else:
                next_day = str(int(current_day) + 1)
                other_month = current_month
                other_year = current_year
            current_date_next_day = (next_day, other_month, other_year)

            print(f'Scraping from {current_date} to {current_date_next_day}')
            self.search(current_date, current_date_next_day)
            scraped_data = self.scrape()
            print(f'Scraped data from {current_date} to {current_date_next_day}')
            data_cleaned = clean_data(scraped_data)

            file_name = ''
            save_to_csv(file_name, data_cleaned)

            current_day = next_day
            current_month = other_month
            current_year = other_year
