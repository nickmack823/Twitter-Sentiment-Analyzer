import os
from os.path import exists
from flask import Flask, render_template, jsonify, request
import json
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoSuchElementException
import main
from sentiment_classifier import get_classifiers, classify_tweets
from apscheduler.schedulers.background import BackgroundScheduler
from plotter import Plotter

classifiers = None


def clear_templates():
    print('Performing scheduled deletion of plot templates...')
    for file_name in os.listdir("templates"):
        if not file_name == "index.html":
            os.remove(os.path.join("templates", file_name))
            print(file_name + " removed.")
    print('Deletion completed.')


clear_templates()
# Create scheduled job to delete generated plot html files every hour
scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(clear_templates, 'interval', hours=24)
scheduler.start()

app = Flask(__name__)

months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September',
          'October', 'November', 'December']
curr_hashtag = None
plot_html = ''
days_completed = 0


def segment_date(date):
    """Splits input date into day, month, and year"""
    day = date[8:] if date[8:][0] != '0' else date[9:]
    month = months[int(date[5:7]) - 1]
    year = date[0:4]

    return day, month, year


def collect_data(hashtag, date_range):
    """Begins data collection for input hashtag and date range."""
    global classifiers, days_completed
    if classifiers is None:
        classifiers = get_classifiers()
    main_obj = main.Main(hashtag, date_range, classifiers)
    try:
        main_obj.collect_tweet_data_for_range()
        progress_generator = main_obj.collect_tweet_data_for_range()
        for n in progress_generator:
            days_completed = n
            update_progress()
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
    global curr_hashtag

    user_input = json.loads(user_input)
    hashtag = user_input[0]
    curr_hashtag = hashtag
    date_range = (segment_date(user_input[1]), segment_date(user_input[2]))
    collect_data(hashtag, date_range)
    return ''


@app.route("/update-progress", methods=['GET', 'POST'])
def update_progress():
    return jsonify(days_completed)


@app.route("/reset-progress", methods=['GET', 'POST'])
def reset_progress():
    global days_completed
    days_completed = 0
    return ''


@app.route("/get-plot", methods=["GET", "POST"])
def get_data_plot():
    print("GET")
    user_input = request.get_json()
    print(user_input)
    hashtag = user_input['hashtag']
    other = user_input['other']
    global plot_html
    try:
        p = Plotter(hashtag)
        if other != '':
            year = int(other[0:4])
            # Month data
            if len(other) == 7:
                month = months[int(other[5:]) - 1]
                plot_html = p.plot_month(month, year)
            else:
                plot_html = p.plot_year(year)
        else:
            plot_html = p.plot_all_days()
    except FileNotFoundError as e:
        print(e)
        plot_html = None

    if plot_html is None:
        return 'false'
    elif exists("templates/" + plot_html):
        return 'true'


@app.route("/plot")
def render_plot():
    if exists("templates/" + plot_html) and plot_html != '':
        return render_template(plot_html)
    else:
        return "ERROR: Data not found."


@app.route("/get-data-files", methods=['GET', 'POST'])
def get_data_files():
    file_list = []
    for file_name in os.listdir("data_files"):
        file_list.append(f"data_files/{file_name}")
    return jsonify(file_list)


@app.route("/classify-tweet", methods=['GET', 'POST'])
def classify_tweet():
    tweet = str(request.get_data())[2:]
    tweet = tweet[:-1]
    global classifiers
    if classifiers is None:
        classifiers = get_classifiers()

    results = classify_tweets([tweet], classifiers)
    results_dict = {}
    for result in results[0]:
        results_dict[result[0]] = result[1]

    return results_dict


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
