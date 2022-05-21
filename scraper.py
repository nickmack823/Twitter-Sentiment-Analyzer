import datetime
import sys
import time
import json
import csv
import pandas
import pycld2
from os.path import exists
from pathlib import Path
from selenium import webdriver
from selenium.common import exceptions
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.wait import WebDriverWait

search_url = 'https://twitter.com/search-advanced'

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

months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September',
          'October', 'November', 'December']


def save_to_csv(file_path, cleaned_data):
    """
    Saves cleaned data to an existing CSV file if one exists, else writes to a new file.
    :param file_path:
    :param cleaned_data:
    :return:
    """
    # Check if file exists already
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


def scrape_displayed_tweet_elements(tweet_elements, collected_elements):
    newly_collected = []
    texts, dates, likes, retweets = [], [], [], []
    # Scrape currently available tweets
    for t in tweet_elements:
        try:
            # Scroll to tweet to ensure all of its elements are loaded, avoiding visited tweets
            if t not in collected_elements:
                newly_collected.append(t)
                texts.append(t.find_element(By.CSS_SELECTOR, "[data-testid='tweetText']").text)
                dates.append(t.find_element(By.CLASS_NAME, classes['dates']).text)
                likes.append(t.find_element(By.CSS_SELECTOR, "[data-testid='like']").text)
                retweets.append(t.find_element(By.CSS_SELECTOR, "[data-testid='retweet']").text)
        except exceptions.StaleElementReferenceException:
            pass

    return texts, dates, likes, retweets, newly_collected


class Scraper:
    # TWITTER CRAWL DELAY: 1 SECOND
    driver, service = None, None

    hashtag = ''
    date_range = tuple()
    file_path = ''
    current_search_year = ''

    # HTML element info
    xpaths, classes = [], []

    def __init__(self, hashtag, date_range):
        self.service = Service(str(chromedriver_path))
        self.hashtag = hashtag
        self.date_range = date_range
        self.file_path = root_path / scraper_dir / f"{self.hashtag}.csv"

    def begin_scraping_process(self):
        self.driver = webdriver.Chrome(service=self.service)
        self.collect_top_tweets_in_range(self.date_range[0], self.date_range[1])
        self.driver.quit()

    def select_date_parameters(self, start_date, end_date):
        start_day, start_month, start_year = start_date
        end_day, end_month, end_year = end_date

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

    def search(self, start_date, end_date):
        """
        Accesses results page from advanced Twitter search with given search parameters, accessing tweets
        that contain the hashtag to search within the given timeframe.
        :param start_date:
        :param end_date:
        :return:
        """
        self.driver.get(search_url)

        these_hashtags = WebDriverWait(self.driver, 20).until \
            (expected_conditions.presence_of_element_located((By.NAME, 'theseHashtags')))
        these_hashtags.send_keys(self.hashtag)

        # mentioning_these_accounts = WebDriverWait(self.driver, 20).until \
        #     (expected_conditions.presence_of_element_located((By.NAME, 'mentioningTheseAccounts')))
        # mentioning_these_accounts.send_keys(mentioning_account)

        scroll = self.driver.find_element(by=By.XPATH, value=xpaths['scroll'])
        self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scroll)

        self.select_date_parameters(start_date, end_date)

        # Parameters set, now search
        search_button = self.driver.find_element(by=By.XPATH, value=xpaths['search_button'])
        search_button.click()

    def reached_end_of_results(self, tweet_element_height, waited_for_load=False):
        page_height = self.driver.execute_script("return document.body.scrollHeight")
        total_scrolled_height = self.driver.execute_script("return window.pageYOffset + window.innerHeight")
        # Check if scrolled to end of page (no further tweets are loading)
        if total_scrolled_height + tweet_element_height >= page_height:
            # Wait for 3 seconds to allow page to load if there is more content
            if not waited_for_load:
                time.sleep(3)
                return self.reached_end_of_results(tweet_element_height, waited_for_load=True)
            else:
                return True

    def scrape(self):
        """
        Scrapes available tweets until parameter limit has been met.
        :return:
        """
        text_data, date_data, likes_data, retweets_data = [], [], [], []
        collected_tweets = []
        scrolled_to = []
        tweet_locations, tweet_heights = [], []
        # While there are still results available, scrape them
        while True:
            # Get HTML elements of currently loaded tweets
            try:
                tweet_elements = WebDriverWait(self.driver, 10).until \
                    (expected_conditions.presence_of_all_elements_located((By.CSS_SELECTOR, "[data-testid='tweet']")))
                # Store last loaded tweet info for later retrieval (preventing StaleElementException)
                last_tweet = tweet_elements[-1]
                tweet_locations.append(last_tweet.location)
                tweet_heights.append(last_tweet.size['height'])
            except TimeoutException as e:
                print(e)
                break
            except StaleElementReferenceException as e:
                print(e)
                # break

            texts, dates, likes, retweets, newly_collected = scrape_displayed_tweet_elements(
                tweet_elements, collected_tweets)
            collected_tweets.extend(newly_collected)

            # Update main data lists
            text_data.extend(texts)
            date_data.extend(dates)
            likes_data.extend(likes)
            retweets_data.extend(retweets)

            if tweet_locations[-1] in scrolled_to:
                results_ended = self.reached_end_of_results(last_tweet.size['height'])
            else:
                last_tweet_location = tweet_locations[-1]
                self.driver.execute_script(f"window.scrollTo({last_tweet_location['x']}, {last_tweet_location['y']})")
                scrolled_to.append(last_tweet_location)
                results_ended = False

            if results_ended:
                print(f'End of results, scraped {len(text_data)} tweets.')
                break

        return text_data, date_data, likes_data, retweets_data

    def clean_data(self, input_data):
        """
        Iterates through input tuple of data lists and cleans them.
        :param input_data: a tuple of lists
        :return: the input tuple with cleaned list elements
        """
        texts_list, dates_list, likes_list, retweets_list = input_data[0], input_data[1], input_data[2], input_data[3]
        output_data = ([], [], [], [])
        non_english_removed, duplicates_removed = 0, 0

        # Iterate through each list
        for n in range(len(texts_list)):
            text = texts_list[n].replace('\n', '')
            # Detect and omit non-English tweets
            try:
                lang_data = pycld2.detect(text)[2]
                if lang_data[0][0] != 'ENGLISH':
                    non_english_removed += 1
                    continue
            except pycld2.error as e:
                print(f'{e}: {text}')

            # Skip duplicates (bot accounts, tweets repeated)
            if text in output_data[0]:
                duplicates_removed += 1
                continue

            # Tweet data cleared for cleaning, now normalize date,
            try:
                today = str(datetime.date.today())
                curr_year = str(int(today[:4]))
                # Append year to date data if searching through current-year tweets (Twitter excludes the year on these)
                if curr_year == self.current_search_year:
                    date = dates_list[n] + f', {self.current_search_year}'
                else:
                    date = dates_list[n]
                likes = likes_list[n]
                retweets = retweets_list[n]
            except IndexError as e:
                print(f'{e}, n={n}: \n'
                      f'{texts_list}'
                      f'{dates_list}'
                      f'{likes_list}'
                      f'{retweets_list}')
                # Reset process and try again, skipping over successfully scraped dates
                self.driver.quit()
                time.sleep(3)
                self.begin_scraping_process()

            # If tweet has no likes/retweets (and thus '' as that value), set value to 0. Else, send string value to
            # integer with commas removed for values >= 1,000
            likes = 0 if likes == '' else int(likes.replace(',', ''))
            retweets = 0 if retweets == '' else int(retweets.replace(',', ''))

            output_data[0].append(text)
            output_data[1].append(date)
            output_data[2].append(likes)
            output_data[3].append(retweets)

        print(f'Data cleaned: {non_english_removed} non-English tweet(s) removed, '
              f'{duplicates_removed} duplicate(s) removed, remaining tweets "likes" and "retweets" data normalized.')

        return output_data

    def tweets_already_collected(self, date):

        if not exists(self.file_path):
            return False

        df = pandas.read_csv(self.file_path)
        dates_col = pandas.Series(df['date'].tolist())
        date_value = f'{date[1][0:3]} {date[0]}, {self.current_search_year}'
        print(f'Checking if {date} already scraped...')
        if date_value in set(dates_col):
            print(f'{date} data already collected.')
            return True
        else:
            return False

    def collect_top_tweets_in_range(self, start, end):
        print(f'Scraping from {start} to {end}')
        start_day, start_month, start_year = start
        end_day, end_month, end_year = end

        current_day, current_month, current_year = start_day, start_month, start_year
        while current_day != end_day or current_month != end_month or current_year != end_year:
            current_date = (current_day, current_month, current_year)
            days_in_current_month = get_days_in_month(current_month, current_year)
            self.current_search_year = current_year

            # Final day of month reached, go to next month
            if days_in_current_month[-1] == current_day:
                if current_month == 'December':
                    other_year = str(int(current_year) + 1)
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

            current_day = next_day
            current_month = other_month
            current_year = other_year

            # Data for this date already collected, go to next day
            if self.tweets_already_collected(current_date):
                continue

            print(f'Scraping from {current_date} to {current_date_next_day}...')
            self.search(current_date, current_date_next_day)
            scraped_data = self.scrape()
            print(f'Scraped data from {current_date} to {current_date_next_day}.')
            data_cleaned = self.clean_data(scraped_data)

            save_to_csv(self.file_path, data_cleaned)

        print(f'Tweets for {start} to {end} scraped, exiting.')

