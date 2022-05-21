import datetime
import time
import threading
from pathlib import Path
from queue import Queue
from scraper import Scraper, get_days_in_month, save_to_csv
from sentiment_classifier import classify
from os.path import exists
import pandas

months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September',
          'October', 'November', 'December']

if __name__ == "__main__":
    # hashtag, from_account, mentioning_account = '', '', '',

    # TODO: Receive parameter inputs
    dates = ('29', 'December', '2021'), ('19', 'March', '2022')
    sample_hashtags = ['abortion', 'vaccines', 'Marvel', 'Batman']
    # for hashtag in sample_hashtags:
    # mentioning_account = ''

    s = Scraper(sample_hashtags[0], dates)

    start_time = time.time()
    s.begin_scraping_process()
    seconds = time.time() - start_time
    runtime = datetime.timedelta(seconds=seconds)
    print(f'Scraping runtime: {runtime}')
    # Getting scraped output

        # # Read newly scraped data
        # file_path = scraper.file_path
        # if not exists(file_path):
        #     exit('Data file does not exist, exiting.')
        # df = pandas.read_csv(file_path)
        # tweet_list = df.loc[:, 'tweet'].tolist()
        #
        # # Determine classifications for each tweet and transform results into a column for DataFrame
        # sentiment_column = classify(tweet_list)
        #
        # # # Append sentiment column to DataFrame and write to CSV
        # df['sentiment'] = pandas.Series(sentiment_column)
        # new_path = Path(str(file_path) + '_classified')
        # df.to_csv(new_path)

