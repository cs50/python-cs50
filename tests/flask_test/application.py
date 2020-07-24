import logging
import os
import requests
import sys

import cs50
import cs50.flask

from flask import Flask, render_template

app = Flask(__name__)

os.environ["WERKZEUG_RUN_MAIN"] = "true"

with open("test.db", "w") as f:
    f.write("")

db_url = "sqlite:///test.db"
db = cs50.SQL(db_url)

@app.route("/")
def index():
    return "flask tests for python-cs50"

@app.route("/autocommit")
def autocommit():
    db.execute("INSERT INTO test (val) VALUES (?)", "def")
    db2 = cs50.SQL(db_url)
    ret = db2.execute("SELECT val FROM test WHERE val=?", "def")
    return str(ret == [{"val": "def"}])

@app.route("/create")
def create():
    ret = db.execute("CREATE TABLE test (id INTEGER PRIMARY KEY AUTOINCREMENT, val VARCHAR(16))")
    return str(ret)

@app.route("/delete")
def delete():
    ret = db.execute("DELETE FROM test")
    return str(ret > 0)

@app.route("/drop")
def drop():
    ret = db.execute("DROP TABLE test")
    return str(ret)

@app.route("/insert")
def insert():
    ret = db.execute("INSERT INTO test (val) VALUES (?)", "abc")
    return str(ret > 0)

@app.route("/multiple_connections")
def multiple_connections():
    ctx = len(app.teardown_appcontext_funcs)
    db1 = cs50.SQL(db_url)
    td1 = (len(app.teardown_appcontext_funcs) == ctx + 1)
    db2 = cs50.SQL(db_url)
    td2 = (len(app.teardown_appcontext_funcs) == ctx + 2)
    return str(td1 and td2)

@app.route("/select")
def select():
    ret = db.execute("SELECT val FROM test")
    return str(ret == [{"val": "abc"}])

@app.route("/single_teardown")
def single_teardown():
    db.execute("SELECT * FROM test")
    ctx = len(app.teardown_appcontext_funcs)
    db.execute("SELECT COUNT(id) FROM test")
    return str(ctx == len(app.teardown_appcontext_funcs))
