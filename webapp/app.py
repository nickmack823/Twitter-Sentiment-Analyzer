from flask import Flask, render_template

app = Flask(__name__)


# To render HTML files, there must be a folder called 'templates' with the files in them.
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/", methods=['POST'])  # For getting form data
def collect_data():
    return render_template('index.html')


# To render static files (static, videos, css files, etc), create 'static' folder and reference things in there

# TO DIRECTLY EDIT A WEBPAGE FROM CHROME ITSELF:
# 1. Inspect --> Console --> document.body.contentEditable=true
# To delete: 'Select element tool' --> del
# TO SAVE CHANGES: CTRL+S --> replace HTML file


if __name__ == '__main__':
    app.run(debug=True)