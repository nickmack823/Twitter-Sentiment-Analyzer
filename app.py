from flask import Flask, render_template
import json
import main

app = Flask(__name__)

months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September',
          'October', 'November', 'December']


def segment_date(date):
    day = date[8:] if date[8:][0] != '0' else date[9:]
    month = months[int(date[5:7]) - 1]
    year = date[0:4]
    return day, month, year


# To render HTML files, there must be a folder called 'templates' with the files in them.
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/data-analysis/<string:user_input>", methods=['POST'])  # For getting input data
def analyze_data(user_input):
    user_input = json.loads(user_input)
    hashtag = user_input[0]
    date_range = (segment_date(user_input[1]), segment_date(user_input[2]))
    # if main.classifiers is None:
    #     main.classifiers = main.get_classifiers()
    # main_obj = Main(hashtag, date_range)
    # main_obj.collect_tweet_data_for_range()


# To render static files (static, videos, css files, etc), create 'static' folder and reference things in there

# TO DIRECTLY EDIT A WEBPAGE FROM CHROME ITSELF:
# 1. Inspect --> Console --> document.body.contentEditable=true
# To delete: 'Select element tool' --> del
# TO SAVE CHANGES: CTRL+S --> replace HTML file


if __name__ == '__main__':
    app.run(debug=True)