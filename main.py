from scraper import Scraper
import sentiment_classifier

if __name__ == "__main__":
    all_these_words, exact_phrase, any_these_words, none_these_words, hashtags = '', '', '', '', ''
    from_accounts, to_accounts, mentioning_accounts = '', '', ''
    min_replies, min_likes, min_retweets = '', '', ''

    # TODO: Receive parameter declarations

    hashtags = 'abortion'
    from_accounts = '@DonaldTrump'

    word_params = (all_these_words, exact_phrase, any_these_words, none_these_words, hashtags)
    account_params = (from_accounts, to_accounts, mentioning_accounts)
    engagement_params = (min_replies, min_likes, min_retweets)

    search_parameters = (word_params, account_params, engagement_params)
    date_range = ('27', 'February', '2022'), ('28', 'March', '2022')

    scraper = Scraper(search_parameters, date_range)
    # begin_scraping_process('abortion', s, e)
    scraper.begin_scraping_process(('27', 'February', '2022'), ('28', 'March', '2022'))