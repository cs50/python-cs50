from cs50 import SQL

db = SQL("sqlite:///sqlite.db")
db.execute("SELECT 1")
