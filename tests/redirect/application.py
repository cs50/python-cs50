import cs50
from flask import Flask, redirect, render_template

app = Flask(__name__)

@app.route("/")
def index():
    return redirect("/foo")

@app.route("/foo")
def foo():
    return render_template("foo.html")
