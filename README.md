# CS50 Library for Python

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

1. In one terminal, execute:

    ```
    cd python-cs50
    docker compose build
    docker compose up
    ```

1. In another terminal, execute:

    ```
    docker exec -it python-cs50 bash -l
    ```

    And then execute, e.g.:

    ```
    python tests/sql.py
    ```

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
