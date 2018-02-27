import sys

sys.path.insert(0, "../src")

import cs50
import requests

def f():
    res = requests.get("cs50.harvard.edu")
f()
