import logging
import sys

sys.path.insert(0, "../src")

import cs50

"""
db = cs50.SQL("sqlite:///foo.db")

logging.getLogger("cs50").disabled = False

#db.execute("SELECT ? FROM ? ORDER BY ?", "a", "tbl", "c")
db.execute("CREATE TABLE IF NOT EXISTS bar (firstname STRING)")

db.execute("INSERT INTO bar VALUES (?)", "baz")
db.execute("INSERT INTO bar VALUES (?)", "qux")
db.execute("SELECT * FROM bar WHERE firstname IN (?)", ("baz", "qux"))
db.execute("DELETE FROM bar")
"""

db = cs50.SQL("postgresql://postgres@localhost/test")

"""
print(db.execute("DROP TABLE IF EXISTS cs50"))
print(db.execute("CREATE TABLE cs50 (id SERIAL PRIMARY KEY, val VARCHAR(16), bin BYTEA)"))
print(db.execute("INSERT INTO cs50 (val) VALUES('foo')"))
print(db.execute("SELECT * FROM cs50"))

print(db.execute("DROP TABLE IF EXISTS cs50"))
print(db.execute("CREATE TABLE cs50 (val VARCHAR(16), bin BYTEA)"))
print(db.execute("INSERT INTO cs50 (val) VALUES('foo')"))
print(db.execute("SELECT * FROM cs50"))
"""

print(db.execute("DROP TABLE IF EXISTS cs50"))
print(db.execute("CREATE TABLE cs50 (id SERIAL PRIMARY KEY, val VARCHAR(16), bin BYTEA)"))
print(db.execute("INSERT INTO cs50 (val) VALUES('foo')"))
print(db.execute("INSERT INTO cs50 (val) VALUES('bar')"))
print(db.execute("INSERT INTO cs50 (val) VALUES('baz')"))
print(db.execute("SELECT * FROM cs50"))
try:
    print(db.execute("INSERT INTO cs50 (id, val) VALUES(1, 'bar')"))
except Exception as e:
    print(e)
    pass
print(db.execute("INSERT INTO cs50 (val) VALUES('qux')"))
#print(db.execute("DELETE FROM cs50"))
