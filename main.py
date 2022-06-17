import csv
import datetime
import os
import threading
from pathlib import Path
from queue import Queue
import pycld2
from scraper import Scraper
from sentiment_classifier import classify
from os.path import exists
import pandas

months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September',
          'October', 'November', 'December']
data_dir = Path('.') / 'static' / 'data_files'

if not os.path.exists(data_dir):
    os.mkdir(data_dir)


class DataProcessingThread(threading.Thread):

    def __init__(self, main_obj):
        threading.Thread.__init__(self)
        self.in_queue = Queue()
        self.main = main_obj

    def run(self):
        while True:
            scraped_data = self.in_queue.get()  # blocking till something is available in the queue
            print('Classification Thread: Processing data...')
            data_cleaned = clean_data(scraped_data)

            sentiments = classify(data_cleaned[0], self.main.classifiers)
            print('Classification Thread: Data classified, saving to CSV...')
            interval_final_data = (data_cleaned[0], data_cleaned[1], data_cleaned[2], data_cleaned[3], sentiments)

            save_to_csv(self.main.data_file_path, interval_final_data)
            self.main.tweets_scraped += len(data_cleaned[0])
            print('Classification Thread: Data saved to CSV, done.')
            if self.main.done_scraping and self.in_queue.qsize() == 0:
                self.main.days_completed += 1
                print('Classification Thread: Closing classification thread.')
                break


def to_numeric(tweet_engagement_value):
    """Sends input tweet like/retweet value to a number."""
    # Non-numeric characters included in some tweet like/retweet values
    non_numeric = [',', '.', 'K', 'M']
    num_string = ''
    for c in tweet_engagement_value:
        if c not in non_numeric:
            num_string += c
        else:
            if c == '.':
                decimals = int(tweet_engagement_value[tweet_engagement_value.index(c) + 1:-1])
                if 'K' in tweet_engagement_value:
                    decimals = decimals * 100
                    num_string = int(num_string) * 1000 + decimals
                elif 'M' in tweet_engagement_value:
                    decimals = decimals * 100000
                    num_string = int(num_string) * 1000000 + decimals
                break

    return int(num_string)


def clean_data(scraped_data):
    """
    Iterates through input tuple of data lists and cleans them.
    """
    texts_list, dates_list, likes_list, retweets_list = scraped_data[0], scraped_data[1], scraped_data[2], scraped_data[3]
    output_data = ([], [], [], [])
    non_english_removed, duplicates_removed = 0, 0

    twitter_start_year = 2006
    curr_year = datetime.date.today().year
    years_of_twitter = [str(curr_year - i) for i in range(curr_year - twitter_start_year + 1)]

    # Iterate through each list to clean texts, dates, likes, and retweets
    for n in range(len(texts_list)):
        text = texts_list[n].replace('\n', '')
        text = ''.join(c for c in text if c.isprintable())  # Attempt to prevent pycld2 error from invalid UTF-8 chars
        # Detect and omit non-English tweets
        try:
            lang_data = pycld2.detect(text)[2]
            if lang_data[0][0] != 'ENGLISH':
                non_english_removed += 1
                continue
        except pycld2.error as e:
            print(f'ERROR {e}: {text}')
            continue

        # Tweet data cleared for cleaning, now normalize date,
        # Append year to date data if searching through current-year tweets (Twitter excludes the year on these)
        if dates_list[n][-4:] not in years_of_twitter:
            date = dates_list[n] + f', {curr_year}'
        else:
            date = dates_list[n]

        # Skip duplicates (tweets repeated on same day)
        if text in output_data[0]:
            i = output_data[0].index(text)
            if output_data[1][i] == date:
                duplicates_removed += 1
                continue

        likes = likes_list[n]
        retweets = retweets_list[n]

        likes = 0 if likes == '' else to_numeric(likes)
        retweets = 0 if retweets == '' else to_numeric(retweets)

        output_data[0].append(text)
        output_data[1].append(date)
        output_data[2].append(likes)
        output_data[3].append(retweets)

    print(f'Data cleaned: {non_english_removed} non-English tweet(s) removed, '
          f'{duplicates_removed} duplicate(s) removed, remaining tweets "likes" and "retweets" data normalized.')
    return output_data


def save_to_csv(file_path, final_data):
    """
    Saves cleaned data to an existing CSV file if one exists, else writes to a new file.
    """
    # Check if file exists already
    file_exists = exists(file_path)
    # If it exists, append data to existing file
    if file_exists:
        # Get existing rows to prevent adding duplicate data
        with open(file_path, 'r', encoding='utf-8') as file1:
            # Existing data
            existing_rows_text = [line[0] for line in csv.reader(file1, delimiter='|')] # Set -t < list -t for lookup
            existing_rows_date = [line[1] for line in csv.reader(file1, delimiter='|')]
            tweet_tuples = {(text, date) for text, date in zip(existing_rows_text, existing_rows_date)}

            # Write to existing file
            with open(file_path, 'a', encoding='utf-8', newline='') as file2:
                writer = csv.writer(file2, delimiter="|")
                duplicates = 0
                for n in range(len(final_data[0])):
                    tweet, date, likes, retweets, sentiment = final_data[0][n], final_data[1][n], final_data[2][n], \
                                                              final_data[3][n], final_data[4][n]
                    row = [tweet, date, likes, retweets, sentiment]
                    # Check if tweet message already tweeted on this date
                    if (tweet, date) not in tweet_tuples:
                        writer.writerow(row)
                    else:
                        duplicates += 1
                print(f'Skipped {duplicates} duplicate rows.')
    else:
        # Write to new CSV (newline set to '' to prevent empty rows between each entry)
        with open(file_path, 'w', encoding='utf-8', newline='') as file3:
            writer = csv.writer(file3, delimiter="|")
            # If writing to new file, add header row
            headers = ['tweet', 'date', 'likes', 'retweets', 'sentiment']
            writer.writerow(headers)
            for n in range(len(final_data[0])):
                tweet, date, likes, retweets, sentiment = final_data[0][n], final_data[1][n], final_data[2][n], \
                                                          final_data[3][n], final_data[4][n]
                row = [tweet, date, likes, retweets, sentiment]
                writer.writerow(row)


def get_days_in_month(month, year):
    """Determines the number of days in the given month."""
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
        days = [str(day) for day in range(1, 32)] if month in months_with_31_days else [str(day) for day in range(1, 31)]

    return days


class Main:

    def __init__(self, selected_hashtag, date_range, classifiers, using_thread=False):
        self.selected_hashtag = selected_hashtag
        self.data_file_path = data_dir / f"{selected_hashtag}.csv"
        self.date_range = date_range
        self.classifiers = classifiers

        self.scraper = Scraper(selected_hashtag)
        self.current_search_year = self.date_range[0][2]

        self.using_thread = using_thread
        if self.using_thread:
            self.data_thread = DataProcessingThread(self)
            self.data_thread.daemon = True
        self.done_scraping = False

        self.days_completed = 0
        self.tweets_scraped = 0

    def day_tweets_already_collected(self, date):
        """Checks if tweets from the input date have already been scraped."""
        if not exists(self.data_file_path):
            return False

        df = pandas.read_csv(self.data_file_path, delimiter="|")
        dates_col = pandas.Series(df['date'].tolist())
        date_value = f'{date[1][0:3]} {date[0]}, {self.current_search_year}'
        if date_value in set(dates_col):
            return True
        else:
            return False

    def collect_tweet_data_for_range(self):
        """Begins data collection process based on this class instance's initialization parameters."""
        start = self.date_range[0]
        end = self.date_range[1]

        # Begin data processing thread
        if self.using_thread:
            self.data_thread.start()

        print(f'Scraping #{self.selected_hashtag} from {start} to {end}')
        start_day, start_month, start_year = start
        end_day, end_month, end_year = end

        # TODO: Implement interval alterations

        current_day, current_month, current_year = start_day, start_month, start_year
        print('Skipping days already scraped...')
        while True:
            current_date = (current_day, current_month, current_year)
            days_in_current_month = get_days_in_month(current_month, current_year)

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

            if current_day == end_day and current_month == end_month and current_year == end_year:
                break

            self.current_search_year = current_year

            current_day = next_day
            current_month = other_month
            current_year = other_year

            # Data for this date already collected, go to next day
            if self.day_tweets_already_collected(current_date):
                self.days_completed += 1
                continue

            print(f'Scraping from {current_date} to {current_date_next_day}...')

            self.scraper.search(current_date, current_date_next_day)
            scraped_data = self.scraper.scrape()
            print('Processing data...')
            if self.using_thread:
                self.data_thread.in_queue.put(scraped_data)
            else:
                data_cleaned = clean_data(scraped_data)
                sentiments = classify(data_cleaned[0], self.classifiers)
                print('Data cleaned and classified, saving to CSV...')
                interval_final_data = (data_cleaned[0], data_cleaned[1], data_cleaned[2], data_cleaned[3], sentiments)

                save_to_csv(self.data_file_path, interval_final_data)
                self.tweets_scraped += len(data_cleaned[0])
                print('Data saved to CSV, done.')
            self.days_completed += 1
            yield self.days_completed

        print(f'Tweets for {start} to {end} scraped, exiting.')
        self.scraper.driver.quit()
        self.done_scraping = True

        return True


