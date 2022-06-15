import os
from os.path import exists
import pandas
from flask import Flask, render_template, jsonify, request
from flask_caching import Cache
import json
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoSuchElementException
import main
from sentiment_classifier import get_classifiers, classify_tweets
from plotter import Plotter

data_files_path = os.path.join("static", "data_files")

months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September',
          'October', 'November', 'December']

app = Flask(__name__)
# Config for Cache
app.config["SECRET_KEY"] = "ajndsisd82h2e"
# app.config["CACHE_TYPE"] = "SimpleCache"
cache = Cache(app, config={
    'CACHE_TYPE': 'FileSystemCache',
    'CACHE_DIR': 'cached',
    'CACHE_DEFAULT_TIMEOUT': 3600})


def clear_templates():
    print('Performing deletion of plot templates...')
    for file_name in os.listdir("templates"):
        if not file_name == "index.html":
            os.remove(os.path.join("templates", file_name))
            print(file_name + " removed.")
    print('Deletion completed.')


def clear_empty_data():
    print('Clearing empty data files...')
    for file_name in os.listdir(data_files_path):
        df = pandas.read_csv(os.path.join(data_files_path, file_name))
        if len(df) == 0:
            os.remove(os.path.join(data_files_path, file_name))
            print(file_name + " removed.")
    print('Deletion completed.')


def clear_cache():
    for file_name in os.listdir('cached'):
        os.remove(os.path.join('cached', file_name))
    print('Cache cleared.')


clear_templates()
clear_empty_data()
clear_cache()


def segment_date(date):
    """Splits input date into day, month, and year"""
    day = date[8:] if date[8:][0] != '0' else date[9:]
    month = months[int(date[5:7]) - 1]
    year = date[0:4]

    return day, month, year


def collect_data(hashtag, date_range):
    """Begins data collection for input hashtag and date range."""
    if cache.get('classifiers') is None:
        cache.set('classifiers', get_classifiers())
    main_obj = main.Main(hashtag, date_range, cache.get('classifiers'))
    try:
        progress_generator = main_obj.collect_tweet_data_for_range()
        for n in progress_generator:
            cache.set('days_completed', n)
        encountered_error = False

    except TimeoutException as e:
        print(f'ERROR: {e}')
        encountered_error = True
    except StaleElementReferenceException as e:
        print(f'ERROR: {e}')
        encountered_error = True
    except NoSuchElementException as e:
        print(f'ERROR: {e}')
        encountered_error = True
    except IndexError as e:
        print(f'ERROR: {e}')
        encountered_error = True

    if encountered_error:
        print('Retrying data collection...')
        main_obj.scraper.driver.quit()
        collect_data(hashtag, date_range)
    else:
        print(f'Data for #{hashtag} during {date_range} collected successfully!')
        return


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/data-analysis/<string:user_input>", methods=['GET', 'POST'])  # For getting input data
def analyze_data(user_input):
    user_input = json.loads(user_input)
    hashtag = user_input[0]
    cache.set('curr_hashtag', hashtag)
    date_range = (segment_date(user_input[1]), segment_date(user_input[2]))
    collect_data(hashtag, date_range)
    return ''


@app.route("/update-progress", methods=['GET', 'POST'])
def update_progress():
    progress = cache.get('days_completed')
    if progress is None:
        progress = 0
        cache.set('days_completed', 0)
    return jsonify(progress)


@app.route("/reset-progress", methods=['GET', 'POST'])
def reset_progress():
    cache.set('days_completed', 0)
    return ''


@app.route("/get-plot", methods=["GET", "POST"])
def get_data_plot():
    user_input = request.get_json()
    hashtag = user_input['hashtag']
    other = user_input['other']
    try:
        p = Plotter(hashtag)
        if other != '':
            year = int(other[0:4])
            # Month data
            if len(other) == 7:
                month = months[int(other[5:]) - 1]
                cache.set('plot_html', p.plot_month(month, year))
            else:
                cache.set('plot_html', p.plot_year(year))
        else:
            cache.set('plot_html', p.plot_all_days())
    except FileNotFoundError as e:
        print(e)
        cache.set('plot_html', None)
    except KeyError as e:
        print(e)
        cache.set('plot_html', None)

    cached_html = cache.get('plot_html')
    if cached_html is None:
        return 'false'
    elif exists("templates/" + cached_html):
        return 'true'


@app.route("/plot")
def render_plot():
    cached_html = cache.get('plot_html')
    if cached_html is None:
        return "ERROR: Data not found."
    plot_path = "templates/" + cached_html
    if exists(plot_path) and cached_html is not None:
        return render_template(cached_html)
    else:
        return "ERROR: Data not found."


@app.route("/get-data-files", methods=['GET', 'POST'])
def get_data_files():
    file_list = []
    for file_name in os.listdir(data_files_path):
        file_list.append(f"{data_files_path}/{file_name}")
    return jsonify(file_list)


@app.route("/classify-tweet", methods=['GET', 'POST'])
def classify_tweet():
    tweet = str(request.get_data())[2:]
    tweet = tweet[:-1]
    if cache.get('classifiers') is None:
        cache.set('classifiers', get_classifiers())

    results = classify_tweets([tweet], cache.get('classifiers'))
    results_dict = {}
    for result in results[0]:
        results_dict[result[0]] = result[1]

    return results_dict


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
