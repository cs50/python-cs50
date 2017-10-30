import requests
from flask import Flask, render_template

import cs50

app = Flask(__name__)

@app.route("/")
def index():
    def f():
        res = requests.get("cs50.harvard.edu")
    f()
    return render_template("index.html")
