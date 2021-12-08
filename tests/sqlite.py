import logging
import sys

sys.path.insert(0, "../src")

from cs50 import SQL

logging.getLogger("cs50").disabled = False

db = SQL("sqlite:///sqlite.db")
db.execute("SELECT 1")

# TODO
#db.execute("SELECT * FROM Employee WHERE FirstName = ?", b'\x00')

db.execute("SELECT * FROM Employee WHERE FirstName = ?", "' OR 1 = 1")

db.execute("SELECT * FROM Employee WHERE FirstName IN (?)", "Andrew")
db.execute("SELECT * FROM Employee WHERE FirstName IN (?)", ["Andrew"])
db.execute("SELECT * FROM Employee WHERE FirstName IN (?)", ("Andrew",))
db.execute("SELECT * FROM Employee WHERE FirstName IN (?)", ["Andrew", "Nancy"])
db.execute("SELECT * FROM Employee WHERE FirstName IN (?)", ("Andrew", "Nancy"))
db.execute("SELECT * FROM Employee WHERE FirstName IN (?)", [])
db.execute("SELECT * FROM Employee WHERE FirstName IN (?)", ())

db.execute("SELECT * FROM Employee WHERE FirstName = ? AND LastName = ?", "Andrew", "Adams")
db.execute("SELECT * FROM Employee WHERE FirstName = ? AND LastName = ?", ["Andrew", "Adams"])
db.execute("SELECT * FROM Employee WHERE FirstName = ? AND LastName = ?", ("Andrew", "Adams"))

db.execute("SELECT * FROM Employee WHERE FirstName = :1 AND LastName = :2", "Andrew", "Adams")
db.execute("SELECT * FROM Employee WHERE FirstName = :1 AND LastName = :2", ["Andrew", "Adams"])
db.execute("SELECT * FROM Employee WHERE FirstName = :1 AND LastName = :2", ("Andrew", "Adams"))

db.execute("SELECT * FROM Employee WHERE FirstName = ':Andrew :Adams'")

db.execute("SELECT * FROM Employee WHERE FirstName = :first AND LastName = :last", first="Andrew", last="Adams")
db.execute("SELECT * FROM Employee WHERE FirstName = :first AND LastName = :last", {"first": "Andrew", "last": "Adams"})

db.execute("SELECT * FROM Employee WHERE FirstName = %s AND LastName = %s", "Andrew", "Adams")
db.execute("SELECT * FROM Employee WHERE FirstName = %s AND LastName = %s", ["Andrew", "Adams"])
db.execute("SELECT * FROM Employee WHERE FirstName = %s AND LastName = %s", ("Andrew", "Adams"))

db.execute("SELECT * FROM Employee WHERE FirstName = %(first)s AND LastName = %(last)s", first="Andrew", last="Adams")
db.execute("SELECT * FROM Employee WHERE FirstName = %(first)s AND LastName = %(last)s", {"first": "Andrew", "last": "Adams"})
