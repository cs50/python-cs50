from flask import Flask, render_template

app = Flask(__name__)

import cs50
import requests
@app.route("/")
def index():
    def f():
        res = requests.get("cs50.harvard.edu")
    f()
    return render_template("index.html")

@app.route("/foo", methods=["POST"])
def foo():
    return ""
