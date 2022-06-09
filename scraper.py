import time
from pathlib import Path

import selenium.common.exceptions
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.wait import WebDriverWait

search_url = 'https://twitter.com/search-advanced'

# File paths
root_path = Path('.')
scraper_dir = 'scraper_files'
data_dir = 'data_files'

locations = {
  "xpaths": {
      "scroll": "//*[@id=\"layers\"]/div[2]/div/div/div/div/div/div[2]/div[2]/div/div/div",
      "from_month": "/html/body/div[1]/div/div/div[1]/div[2]/div/div/div/div/div/div[2]/div[2]/div/div/div/div[2]/div/div[16]/div/div[2]/div/div[1]/select",
      "from_day": "/html/body/div[1]/div/div/div[1]/div[2]/div/div/div/div/div/div[2]/div[2]/div/div/div/div[2]/div/div[16]/div/div[2]/div/div[2]/select",
      "from_year": "/html/body/div[1]/div/div/div[1]/div[2]/div/div/div/div/div/div[2]/div[2]/div/div/div/div[2]/div/div[16]/div/div[2]/div/div[3]/select",
      "to_month": "/html/body/div[1]/div/div/div[1]/div[2]/div/div/div/div/div/div[2]/div[2]/div/div/div/div[2]/div/div[16]/div/div[4]/div/div[1]/select",
      "to_day": "/html/body/div[1]/div/div/div[1]/div[2]/div/div/div/div/div/div[2]/div[2]/div/div/div/div[2]/div/div[16]/div/div[4]/div/div[2]/select",
      "to_year": "/html/body/div[1]/div/div/div[1]/div[2]/div/div/div/div/div/div[2]/div[2]/div/div/div/div[2]/div/div[16]/div/div[4]/div/div[3]/select",
      "search_button": "//*[@id=\"layers\"]/div[2]/div/div/div/div/div/div[2]/div[2]/div/div/div/div[1]/div/div/div/div/div/div[3]/div"
    },
  "classes": {
    "dates": "css-4rbku5.css-18t94o4.css-901oao.r-14j79pv.r-1loqt21.r-1q142lx.r-37j5jr.r-a023e6.r-16dba41.r-rjixqe.r-bcqeeo.r-3s2u2q.r-qvutc0"
  }
}

# if not exists(html_locations_path):
#     sys.exit('Locations JSON file missing, unable to continue.')

# Get HTML elements' info
xpaths = locations['xpaths']
classes = locations['classes']


def scrape_displayed_tweet_elements(tweet_elements, collected_elements):
    newly_collected = []
    texts, dates, likes, retweets = [], [], [], []
    # Scrape currently available tweets
    for t in tweet_elements:
        # Scroll to tweet to ensure all of its elements are loaded, avoiding visited tweets
        if t not in collected_elements:
            newly_collected.append(t)
            texts.append(t.find_element(By.CSS_SELECTOR, "[data-testid='tweetText']").text)
            dates.append(t.find_element(By.CLASS_NAME, classes['dates']).text)
            likes.append(t.find_element(By.CSS_SELECTOR, "[data-testid='like']").text)
            retweets.append(t.find_element(By.CSS_SELECTOR, "[data-testid='retweet']").text)

    return texts, dates, likes, retweets, newly_collected


class Scraper:

    def __init__(self, hashtag):
        self.hashtag = hashtag
        self.file_path = root_path / data_dir / f"{self.hashtag}.csv"
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

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

        # try:
        these_hashtags = WebDriverWait(self.driver, 20).until \
            (expected_conditions.presence_of_element_located((By.NAME, 'theseHashtags')))
        these_hashtags.send_keys(self.hashtag)

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
        times_checked_results_ended = 0
        # While there are still results available, scrape them
        while True:
            # Get HTML elements of currently loaded tweets
            try:
                tweet_elements = WebDriverWait(self.driver, 10).until \
                    (expected_conditions.presence_of_all_elements_located((By.CSS_SELECTOR, "[data-testid='tweet']")))
            except selenium.common.exceptions.TimeoutException:
                print(f'End of results, scraped {len(text_data)} tweets.')
                break

            # Store last loaded tweet info for later retrieval (preventing StaleElementException)
            last_tweet = tweet_elements[-1]
            tweet_locations.append(last_tweet.location)
            tweet_heights.append(last_tweet.size['height'])

            texts, dates, likes, retweets, newly_collected = scrape_displayed_tweet_elements(
                tweet_elements, collected_tweets)
            collected_tweets.extend(newly_collected)

            # Update main data lists
            text_data.extend(texts)
            date_data.extend(dates)
            likes_data.extend(likes)
            retweets_data.extend(retweets)

            if tweet_locations[-1] in scrolled_to:
                results_ended = self.reached_end_of_results(tweet_heights[-1])
                times_checked_results_ended += 1
                # Looping begins after page with small number of results, break to continue
                if times_checked_results_ended >= 500:
                    break
            else:
                last_tweet_location = tweet_locations[-1]
                self.driver.execute_script(f"window.scrollTo({last_tweet_location['x']}, {last_tweet_location['y']})")
                scrolled_to.append(last_tweet_location)
                results_ended = False

            if results_ended:
                print(f'End of results, scraped {len(text_data)} tweets.')
                break

        return text_data, date_data, likes_data, retweets_data
