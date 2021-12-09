# CS50 Library for Python

[![Build Status](https://travis-ci.com/cs50/python-cs50.svg?branch=master)](https://travis-ci.org/cs50/python-cs50)

## Installation

```
pip3 install cs50
```

## Usage

```
import cs50

...

f = cs50.get_float();
i = cs50.get_int();
s = cs50.get_string();
```

## Testing

1. Run `cli50` in `python-cs50`.
1. Run `sudo su -`.
1. Run `apt install -y libmysqlclient-dev mysql-server postgresql`.
1. Run `pip3 install mysqlclient psycopg2-binary`.
1. In `/etc/mysql/mysql.conf.d/mysqld.cnf`, add `skip-grant-tables` under `[mysqld]`.
1. In `/etc/profile.d/cli.sh`, remove `valgrind` function for now.
1. Run `service mysql start`.
1. Run `mysql -e 'CREATE DATABASE IF NOT EXISTS test;'`.
1. In `/etc/postgresql/12/main/pg_hba.conf, change:
   ```
   local   all             postgres                                peer
   host    all             all             127.0.0.1/32            md5
   ```
   to:
   ```
   local   all             postgres                                trust
   host    all             all             127.0.0.1/32            trust
   ```
1. Run `service postgresql start`.
1. Run `psql -c 'create database test;' -U postgres`.

### Sample Tests

```
import cs50
db = cs50.SQL("sqlite:///foo.db")
db.execute("CREATE TABLE IF NOT EXISTS cs50 (id INTEGER PRIMARY KEY, val TEXT, bin BLOB)")
db.execute("INSERT INTO cs50 (val) VALUES('a')")
db.execute("INSERT INTO cs50 (val) VALUES('b')")
db.execute("BEGIN")
db.execute("INSERT INTO cs50 (val) VALUES('c')")
db.execute("INSERT INTO cs50 (val) VALUES('x')")
db.execute("INSERT INTO cs50 (val) VALUES('y')")
db.execute("ROLLBACK")
db.execute("INSERT INTO cs50 (val) VALUES('z')")
db.execute("COMMIT")

---

import cs50
db = cs50.SQL("mysql://root@localhost/test")
db.execute("CREATE TABLE IF NOT EXISTS cs50 (id INTEGER PRIMARY KEY, val TEXT, bin BLOB)")
db.execute("INSERT INTO cs50 (val) VALUES('a')")
db.execute("INSERT INTO cs50 (val) VALUES('b')")
db.execute("BEGIN")
db.execute("INSERT INTO cs50 (val) VALUES('c')")
db.execute("INSERT INTO cs50 (val) VALUES('x')")
db.execute("INSERT INTO cs50 (val) VALUES('y')")
db.execute("ROLLBACK")
db.execute("INSERT INTO cs50 (val) VALUES('z')")
db.execute("COMMIT")

---

import cs50
db = cs50.SQL("postgresql://postgres@localhost/test")
db.execute("CREATE TABLE IF NOT EXISTS cs50 (id SERIAL PRIMARY KEY, val VARCHAR(16), bin BYTEA)")
db.execute("INSERT INTO cs50 (val) VALUES('a')")
db.execute("INSERT INTO cs50 (val) VALUES('b')")
db.execute("BEGIN")
db.execute("INSERT INTO cs50 (val) VALUES('c')")
db.execute("INSERT INTO cs50 (val) VALUES('x')")
db.execute("INSERT INTO cs50 (val) VALUES('y')")
db.execute("ROLLBACK")
db.execute("INSERT INTO cs50 (val) VALUES('z')")
db.execute("COMMIT")
```
