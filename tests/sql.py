import logging
import sys
import unittest
import warnings

sys.path.insert(0, "../src")

from cs50.sql import SQL

class SQLTests(unittest.TestCase):

    def test_multiple_statements(self):
        self.assertRaises(RuntimeError, self.db.execute, "INSERT INTO cs50(val) VALUES('baz'); INSERT INTO cs50(val) VALUES('qux')")

    def test_delete_returns_affected_rows(self):
        rows = [
            {"id": 1, "val": "foo"},
            {"id": 2, "val": "bar"},
            {"id": 3, "val": "baz"}
        ]
        for row in rows:
            self.db.execute("INSERT INTO cs50(val) VALUES(:val);", val=row["val"])
        self.assertEqual(self.db.execute("DELETE FROM cs50 WHERE id = :id", id=rows[0]["id"]), 1)
        self.assertEqual(self.db.execute("DELETE FROM cs50 WHERE id = :a or id = :b", a=rows[1]["id"], b=rows[2]["id"]), 2)
        self.assertEqual(self.db.execute("DELETE FROM cs50 WHERE id = -50"), 0)

    def test_insert_returns_last_row_id(self):
        self.assertEqual(self.db.execute("INSERT INTO cs50(val) VALUES('foo')"), 1)
        self.assertEqual(self.db.execute("INSERT INTO cs50(val) VALUES('bar')"), 2)

    def test_select_all(self):
        self.assertEqual(self.db.execute("SELECT * FROM cs50"), [])

        rows = [
            {"id": 1, "val": "foo"},
            {"id": 2, "val": "bar"},
            {"id": 3, "val": "baz"}
        ]
        for row in rows:
            self.db.execute("INSERT INTO cs50(val) VALUES(:val)", val=row["val"])

        self.assertEqual(self.db.execute("SELECT * FROM cs50"), rows)

    def test_select_cols(self):
        rows = [
            {"val": "foo"},
            {"val": "bar"},
            {"val": "baz"}
        ]
        for row in rows:
            self.db.execute("INSERT INTO cs50(val) VALUES(:val)", val=row["val"])

        self.assertEqual(self.db.execute("SELECT val FROM cs50"), rows)

    def test_select_where(self):
        rows = [
            {"id": 1, "val": "foo"},
            {"id": 2, "val": "bar"},
            {"id": 3, "val": "baz"}
        ]
        for row in rows:
            self.db.execute("INSERT INTO cs50(val) VALUES(:val)", val=row["val"])

        self.assertEqual(self.db.execute("SELECT * FROM cs50 WHERE id = :id OR val = :val", id=rows[1]["id"], val=rows[2]["val"]), rows[1:3])

    def test_select_with_comments(self):
        self.assertEqual(self.db.execute("--comment\nSELECT * FROM cs50;\n--comment"), [])

    def test_update_returns_affected_rows(self):
        rows = [
            {"id": 1, "val": "foo"},
            {"id": 2, "val": "bar"},
            {"id": 3, "val": "baz"}
        ]
        for row in rows:
            self.db.execute("INSERT INTO cs50(val) VALUES(:val)", val=row["val"])

        self.assertEqual(self.db.execute("UPDATE cs50 SET val = 'foo' WHERE id > 1"), 2)
        self.assertEqual(self.db.execute("UPDATE cs50 SET val = 'foo' WHERE id = -50"), 0)

    def test_string_literal_with_colon(self):
        rows = [
            {"id": 1, "val": ":foo"},
            {"id": 2, "val": "foo:bar"},
            {"id": 3, "val": "  :baz"},
            {"id": 3, "val": ":bar :baz"},
            {"id": 3, "val": "  :bar :baz"}
        ]
        for row in rows:
            self.db.execute("INSERT INTO cs50(val) VALUES(:val)", val=row["val"])

        self.assertEqual(self.db.execute("SELECT val FROM cs50 WHERE val = ':foo'"), [{"val": ":foo"}])
        self.assertEqual(self.db.execute("SELECT val FROM cs50 WHERE val = ':bar'"), [])
        self.assertEqual(self.db.execute("SELECT val FROM cs50 WHERE val = 'foo:bar'"), [{"val": "foo:bar"}])
        self.assertEqual(self.db.execute("SELECT val FROM cs50 WHERE val = '  :baz'"), [{"val": "  :baz"}])
        self.assertEqual(self.db.execute("SELECT val FROM cs50 WHERE val = ':bar :baz'"), [{"val": ":bar :baz"}])
        self.assertEqual(self.db.execute("SELECT val FROM cs50 WHERE val = '  :bar :baz'"), [{"val": "  :bar :baz"}])

    def tearDown(self):
        self.db.execute("DROP TABLE cs50")

    @classmethod
    def tearDownClass(self):
        try:
            self.db.execute("DROP TABLE IF EXISTS cs50")
        except Warning as e:
            # suppress "unknown table"
            if not str(e).startswith("(1051"):
                raise e

class MySQLTests(SQLTests):
    @classmethod
    def setUpClass(self):
        self.db = SQL("mysql://root@localhost/test")

    def setUp(self):
        self.db.execute("CREATE TABLE cs50 (id INTEGER NOT NULL AUTO_INCREMENT, val VARCHAR(16), PRIMARY KEY (id))")

class PostgresTests(SQLTests):
    @classmethod
    def setUpClass(self):
        self.db = SQL("postgresql://postgres@localhost/test")

    def setUp(self):
        self.db.execute("CREATE TABLE cs50 (id SERIAL PRIMARY KEY, val VARCHAR(16))")

class SQLiteTests(SQLTests):
    @classmethod
    def setUpClass(self):
        open("test.db", "w").close()
        self.db = SQL("sqlite:///test.db")
        open("test1.db", "w").close()
        self.db1 = SQL("sqlite:///test1.db", foreign_keys=True)

    def setUp(self):
        self.db.execute("DROP TABLE IF EXISTS cs50")
        self.db.execute("CREATE TABLE cs50(id INTEGER PRIMARY KEY, val TEXT)")

    def test_foreign_key_support(self):
        self.db.execute("DROP TABLE IF EXISTS foo")
        self.db.execute("CREATE TABLE foo(id INTEGER PRIMARY KEY)")
        self.db.execute("DROP TABLE IF EXISTS bar")
        self.db.execute("CREATE TABLE bar(foo_id INTEGER, FOREIGN KEY (foo_id) REFERENCES foo(id))")
        self.assertEqual(self.db.execute("INSERT INTO bar VALUES(50)"), 1)

        self.db1.execute("DROP TABLE IF EXISTS foo")
        self.db1.execute("CREATE TABLE foo(id INTEGER PRIMARY KEY)")
        self.db1.execute("DROP TABLE IF EXISTS bar")
        self.db1.execute("CREATE TABLE bar(foo_id INTEGER, FOREIGN KEY (foo_id) REFERENCES foo(id))")
        self.assertEqual(self.db1.execute("INSERT INTO bar VALUES(50)"), None)


    def test_qmark(self):
        self.db.execute("DROP TABLE IF EXISTS foo")
        self.db.execute("CREATE TABLE foo (firstname STRING, lastname STRING)")

        self.db.execute("INSERT INTO foo VALUES (?, 'bar')", "baz")
        self.assertEqual(self.db.execute("SELECT * FROM foo"), [{"firstname": "baz", "lastname": "bar"}])
        self.db.execute("DELETE FROM foo")

        self.db.execute("INSERT INTO foo VALUES ('bar', ?)", "baz")
        self.assertEqual(self.db.execute("SELECT * FROM foo"), [{"firstname": "bar", "lastname": "baz"}])
        self.db.execute("DELETE FROM foo")

        self.db.execute("INSERT INTO foo VALUES (?, ?)", "bar", "baz")
        self.assertEqual(self.db.execute("SELECT * FROM foo"), [{"firstname": "bar", "lastname": "baz"}])

        self.db.execute("INSERT INTO foo VALUES ('qux', 'quux')")
        self.assertEqual(self.db.execute("SELECT * FROM foo WHERE firstname = ?", 'qux'), [{"firstname": "qux", "lastname": "quux"}])
        self.assertEqual(self.db.execute("SELECT * FROM foo WHERE firstname = ? AND lastname = ?", "qux", "quux"), [{"firstname": "qux", "lastname": "quux"}])
        self.assertEqual(self.db.execute("SELECT * FROM foo WHERE firstname = ? AND lastname = ?", ("qux", "quux")), [{"firstname": "qux", "lastname": "quux"}])
        self.assertEqual(self.db.execute("SELECT * FROM foo WHERE firstname = ? AND lastname = ?", ["qux", "quux"]), [{"firstname": "qux", "lastname": "quux"}])
        self.db.execute("DELETE FROM foo")

        self.db.execute("INSERT INTO foo VALUES (?, ?)", ("bar", "baz"))
        self.assertEqual(self.db.execute("SELECT * FROM foo"), [{"firstname": "bar", "lastname": "baz"}])
        self.db.execute("DELETE FROM foo")

        self.db.execute("INSERT INTO foo VALUES (?, ?)", ["bar", "baz"])
        self.assertEqual(self.db.execute("SELECT * FROM foo"), [{"firstname": "bar", "lastname": "baz"}])
        self.db.execute("DELETE FROM foo")


        self.db.execute("INSERT INTO foo VALUES (?,?)", "bar", "baz")
        self.assertEqual(self.db.execute("SELECT * FROM foo"), [{"firstname": "bar", "lastname": "baz"}])
        self.db.execute("DELETE FROM foo")

        self.db.execute("DROP TABLE IF EXISTS bar")
        self.db.execute("CREATE TABLE bar (firstname STRING)")
        self.db.execute("INSERT INTO bar VALUES (?)", "baz")
        self.assertEqual(self.db.execute("SELECT * FROM bar"), [{"firstname": "baz"}])

        self.assertRaises(RuntimeError, self.db.execute, "INSERT INTO foo VALUES (?)")
        self.assertRaises(RuntimeError, self.db.execute, "INSERT INTO foo VALUES (?, ?)")
        # self.assertRaises(RuntimeError, self.db.execute, "INSERT INTO foo VALUES (?)", ('bar', 'baz'))
        # self.assertRaises(RuntimeError, self.db.execute, "INSERT INTO foo VALUES (?)", ['bar', 'baz'])
        self.assertRaises(RuntimeError, self.db.execute, "INSERT INTO foo VALUES (?, ?)", 'bar', 'baz', 'qux')
        self.assertRaises(RuntimeError, self.db.execute, "INSERT INTO foo VALUES (?, ?)", ('bar', 'baz', 'qux'))
        self.assertRaises(RuntimeError, self.db.execute, "INSERT INTO foo VALUES (?, ?)", ['bar', 'baz', 'qux'])
        self.assertRaises(RuntimeError, self.db.execute, "INSERT INTO foo VALUES (?, ?)", 'bar', baz='baz')

    def test_named(self):
        self.db.execute("DROP TABLE IF EXISTS foo")
        self.db.execute("CREATE TABLE foo (firstname STRING, lastname STRING)")

        self.db.execute("INSERT INTO foo VALUES (:baz, 'bar')", baz="baz")
        self.assertEqual(self.db.execute("SELECT * FROM foo"), [{"firstname": "baz", "lastname": "bar"}])
        self.db.execute("DELETE FROM foo")

        self.db.execute("INSERT INTO foo VALUES ('bar', :baz)", baz="baz")
        self.assertEqual(self.db.execute("SELECT * FROM foo"), [{"firstname": "bar", "lastname": "baz"}])
        self.db.execute("DELETE FROM foo")

        self.db.execute("INSERT INTO foo VALUES (:bar, :baz)", bar="bar", baz="baz")
        self.assertEqual(self.db.execute("SELECT * FROM foo"), [{"firstname": "bar", "lastname": "baz"}])

        self.db.execute("INSERT INTO foo VALUES ('qux', 'quux')")
        self.assertEqual(self.db.execute("SELECT * FROM foo WHERE firstname = :qux", qux='qux'), [{"firstname": "qux", "lastname": "quux"}])
        self.assertEqual(self.db.execute("SELECT * FROM foo WHERE firstname = :qux AND lastname = :quux", qux="qux", quux="quux"), [{"firstname": "qux", "lastname": "quux"}])
        self.db.execute("DELETE FROM foo")

        self.db.execute("INSERT INTO foo VALUES (:bar,:baz)", bar="bar", baz="baz")
        self.assertEqual(self.db.execute("SELECT * FROM foo"), [{"firstname": "bar", "lastname": "baz"}])
        self.db.execute("DELETE FROM foo")

        self.db.execute("DROP TABLE IF EXISTS bar")
        self.db.execute("CREATE TABLE bar (firstname STRING)")
        self.db.execute("INSERT INTO bar VALUES (:baz)", baz="baz")
        self.assertEqual(self.db.execute("SELECT * FROM bar"), [{"firstname": "baz"}])

        self.assertRaises(RuntimeError, self.db.execute, "INSERT INTO foo VALUES (:bar)")
        self.assertRaises(RuntimeError, self.db.execute, "INSERT INTO foo VALUES (:bar, :baz)")
        self.assertRaises(RuntimeError, self.db.execute, "INSERT INTO foo VALUES (:bar, :baz)", bar='bar', baz='baz', qux='qux')
        self.assertRaises(RuntimeError, self.db.execute, "INSERT INTO foo VALUES (:bar, :baz)", 'baz', bar='bar')


    def test_numeric(self):
        self.db.execute("DROP TABLE IF EXISTS foo")
        self.db.execute("CREATE TABLE foo (firstname STRING, lastname STRING)")

        self.db.execute("INSERT INTO foo VALUES (:1, 'bar')", "baz")
        self.assertEqual(self.db.execute("SELECT * FROM foo"), [{"firstname": "baz", "lastname": "bar"}])
        self.db.execute("DELETE FROM foo")

        self.db.execute("INSERT INTO foo VALUES ('bar', :1)", "baz")
        self.assertEqual(self.db.execute("SELECT * FROM foo"), [{"firstname": "bar", "lastname": "baz"}])
        self.db.execute("DELETE FROM foo")

        self.db.execute("INSERT INTO foo VALUES (:1, :2)", "bar", "baz")
        self.assertEqual(self.db.execute("SELECT * FROM foo"), [{"firstname": "bar", "lastname": "baz"}])

        self.db.execute("INSERT INTO foo VALUES ('qux', 'quux')")
        self.assertEqual(self.db.execute("SELECT * FROM foo WHERE firstname = :1", 'qux'), [{"firstname": "qux", "lastname": "quux"}])
        self.assertEqual(self.db.execute("SELECT * FROM foo WHERE firstname = :1 AND lastname = :2", "qux", "quux"), [{"firstname": "qux", "lastname": "quux"}])
        self.assertEqual(self.db.execute("SELECT * FROM foo WHERE firstname = :1 AND lastname = :2", ("qux", "quux")), [{"firstname": "qux", "lastname": "quux"}])
        self.assertEqual(self.db.execute("SELECT * FROM foo WHERE firstname = :1 AND lastname = :2", ["qux", "quux"]), [{"firstname": "qux", "lastname": "quux"}])
        self.db.execute("DELETE FROM foo")

        self.db.execute("INSERT INTO foo VALUES (:1, :2)", ("bar", "baz"))
        self.assertEqual(self.db.execute("SELECT * FROM foo"), [{"firstname": "bar", "lastname": "baz"}])
        self.db.execute("DELETE FROM foo")

        self.db.execute("INSERT INTO foo VALUES (:1, :2)", ["bar", "baz"])
        self.assertEqual(self.db.execute("SELECT * FROM foo"), [{"firstname": "bar", "lastname": "baz"}])
        self.db.execute("DELETE FROM foo")


        self.db.execute("INSERT INTO foo VALUES (:1,:2)", "bar", "baz")
        self.assertEqual(self.db.execute("SELECT * FROM foo"), [{"firstname": "bar", "lastname": "baz"}])
        self.db.execute("DELETE FROM foo")

        self.db.execute("DROP TABLE IF EXISTS bar")
        self.db.execute("CREATE TABLE bar (firstname STRING)")
        self.db.execute("INSERT INTO bar VALUES (:1)", "baz")
        self.assertEqual(self.db.execute("SELECT * FROM bar"), [{"firstname": "baz"}])

        self.assertRaises(RuntimeError, self.db.execute, "INSERT INTO foo VALUES (:1)")
        self.assertRaises(RuntimeError, self.db.execute, "INSERT INTO foo VALUES (:1, :2)")
        self.assertRaises(RuntimeError, self.db.execute, "INSERT INTO foo VALUES (:1, :2)", 'bar', 'baz', 'qux')
        self.assertRaises(RuntimeError, self.db.execute, "INSERT INTO foo VALUES (:1, :2)", 'bar', baz='baz')


if __name__ == "__main__":
    suite = unittest.TestSuite([
        unittest.TestLoader().loadTestsFromTestCase(SQLiteTests),
        unittest.TestLoader().loadTestsFromTestCase(MySQLTests),
        unittest.TestLoader().loadTestsFromTestCase(PostgresTests)
    ])

    logging.getLogger("cs50").disabled = True
    sys.exit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
