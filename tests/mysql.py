import sys

sys.path.insert(0, "../src")

from cs50 import SQL

db = SQL("mysql://root@localhost/test")
db.execute("SELECT 1")
