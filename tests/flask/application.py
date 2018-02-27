import requests
import sys
from flask import Flask, render_template

sys.path.insert(0, "../../src")

import cs50

app = Flask(__name__)

@app.route("/")
def index():
    def f():
        res = requests.get("cs50.harvard.edu")
    f()
    return render_template("index.html")
