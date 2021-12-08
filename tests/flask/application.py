import requests
import sys
from flask import Flask, render_template

sys.path.insert(0, "../../src")

import cs50
import cs50.flask

app = Flask(__name__)

db = cs50.SQL("sqlite:///../sqlite.db")

@app.route("/")
def index():
    db.execute("SELECT 1")
    """
    def f():
        res = requests.get("cs50.harvard.edu")
    f()
    """
    return render_template("index.html")
