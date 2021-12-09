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
            {"id": 1, "val": "foo", "bin": None},
            {"id": 2, "val": "bar", "bin": None},
            {"id": 3, "val": "baz", "bin": None}
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

        self.assertEqual(self.db.execute("SELECT id, val FROM cs50 WHERE id = :id OR val = :val", id=rows[1]["id"], val=rows[2]["val"]), rows[1:3])

    def test_select_with_comments(self):
        self.assertEqual(self.db.execute("--comment\nSELECT * FROM cs50;\n--comment"), [])

    def test_select_with_semicolon(self):
        self.assertEqual(self.db.execute("SELECT * FROM cs50;\n--comment"), [])

    def test_select_with_comments(self):
        self.assertEqual(self.db.execute("--comment\nSELECT * FROM cs50;\n--comment"), [])

    def test_select_with_semicolon(self):
        self.assertEqual(self.db.execute("SELECT * FROM cs50;\n--comment"), [])

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

    def test_blob(self):
        rows = [
            {"id": 1, "bin": b"\0"},
            {"id": 2, "bin": b"\1"},
            {"id": 3, "bin": b"\2"}
        ]
        for row in rows:
            self.db.execute("INSERT INTO cs50(bin) VALUES(:bin)", bin=row["bin"])
        self.assertEqual(self.db.execute("SELECT id, bin FROM cs50"), rows)

    def test_commit(self):
        self.db.execute("BEGIN")
        self.db.execute("INSERT INTO cs50 (val) VALUES('foo')")
        self.db.execute("COMMIT")
        self.assertEqual(self.db.execute("SELECT val FROM cs50"), [{"val": "foo"}])

    def test_rollback(self):
        self.db.execute("BEGIN")
        self.db.execute("INSERT INTO cs50 (val) VALUES('foo')")
        self.db.execute("INSERT INTO cs50 (val) VALUES('bar')")
        self.db.execute("ROLLBACK")
        self.assertEqual(self.db.execute("SELECT val FROM cs50"), [])

    def test_identifier_case(self):
        self.assertIn("count", self.db.execute("SELECT 1 AS count")[0])

    def test_lastrowid(self):
        self.db.execute("CREATE TABLE foo(id SERIAL PRIMARY KEY, firstname TEXT, lastname TEXT)")
        self.assertEqual(self.db.execute("INSERT INTO foo (firstname, lastname) VALUES('firstname', 'lastname')"), 1)
        self.assertRaises(ValueError, self.db.execute, "INSERT INTO foo (id, firstname, lastname) VALUES(1, 'firstname', 'lastname')")

    def tearDown(self):
        self.db.execute("DROP TABLE cs50")
        self.db.execute("DROP TABLE IF EXISTS foo")
        self.db.execute("DROP TABLE IF EXISTS bar")

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
        self.db = SQL("mysql://root@127.0.0.1/test")

    def setUp(self):
        self.db.execute("CREATE TABLE IF NOT EXISTS cs50 (id INTEGER NOT NULL AUTO_INCREMENT, val VARCHAR(16), bin BLOB, PRIMARY KEY (id))")
        self.db.execute("DELETE FROM cs50")


class PostgresTests(SQLTests):
    @classmethod
    def setUpClass(self):
        self.db = SQL("postgresql://postgres:postgres@127.0.0.1/test")

    def setUp(self):
        self.db.execute("CREATE TABLE IF NOT EXISTS cs50 (id SERIAL PRIMARY KEY, val VARCHAR(16), bin BYTEA)")
        self.db.execute("DELETE FROM cs50")


    def test_cte(self):
        self.assertEqual(self.db.execute("WITH foo AS ( SELECT 1 AS bar ) SELECT bar FROM foo"), [{"bar": 1}])


class SQLiteTests(SQLTests):

    @classmethod
    def setUpClass(self):
        open("test.db", "w").close()
        self.db = SQL("sqlite:///test.db")

    def setUp(self):
        self.db.execute("CREATE TABLE IF NOT EXISTS cs50 (id INTEGER PRIMARY KEY, val TEXT, bin BLOB)")
        self.db.execute("DELETE FROM cs50")

    def test_lastrowid(self):
        self.db.execute("CREATE TABLE foo(id INTEGER PRIMARY KEY AUTOINCREMENT, firstname TEXT, lastname TEXT)")
        self.assertEqual(self.db.execute("INSERT INTO foo (firstname, lastname) VALUES('firstname', 'lastname')"), 1)
        self.assertRaises(ValueError, self.db.execute, "INSERT INTO foo (id, firstname, lastname) VALUES(1, 'firstname', 'lastname')")
        self.assertEqual(self.db.execute("INSERT OR IGNORE INTO foo (id, firstname, lastname) VALUES(1, 'firstname', 'lastname')"), None)

    def test_integrity_constraints(self):
        self.db.execute("CREATE TABLE foo(id INTEGER PRIMARY KEY)")
        self.assertEqual(self.db.execute("INSERT INTO foo VALUES(1)"), 1)
        self.assertRaises(ValueError, self.db.execute, "INSERT INTO foo VALUES(1)")

    def test_foreign_key_support(self):
        self.db.execute("CREATE TABLE foo(id INTEGER PRIMARY KEY)")
        self.db.execute("CREATE TABLE bar(foo_id INTEGER, FOREIGN KEY (foo_id) REFERENCES foo(id))")
        self.assertRaises(ValueError, self.db.execute, "INSERT INTO bar VALUES(50)")

    def test_qmark(self):
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
        self.db.execute("DELETE FROM foo")

        self.db.execute("INSERT INTO foo VALUES (?)", ("bar", "baz"))
        self.assertEqual(self.db.execute("SELECT * FROM foo"), [{"firstname": "bar", "lastname": "baz"}])
        self.db.execute("DELETE FROM foo")

        self.db.execute("INSERT INTO foo VALUES (?)", ["bar", "baz"])
        self.assertEqual(self.db.execute("SELECT * FROM foo"), [{"firstname": "bar", "lastname": "baz"}])
        self.db.execute("DELETE FROM foo")

        self.db.execute("INSERT INTO foo VALUES (?,?)", "bar", "baz")
        self.assertEqual(self.db.execute("SELECT * FROM foo"), [{"firstname": "bar", "lastname": "baz"}])
        self.db.execute("DELETE FROM foo")

        self.db.execute("CREATE TABLE bar (firstname STRING)")

        self.db.execute("INSERT INTO bar VALUES (?)", "baz")
        self.assertEqual(self.db.execute("SELECT * FROM bar"), [{"firstname": "baz"}])
        self.db.execute("DELETE FROM bar")

        self.db.execute("INSERT INTO bar VALUES (?)", "baz")
        self.db.execute("INSERT INTO bar VALUES (?)", "qux")
        self.assertEqual(self.db.execute("SELECT * FROM bar WHERE firstname IN (?)", ("baz", "qux")), [{"firstname": "baz"}, {"firstname": "qux"}])
        self.db.execute("DELETE FROM bar")

        self.db.execute("INSERT INTO bar VALUES (?)", "baz")
        self.db.execute("INSERT INTO bar VALUES (?)", "qux")
        self.assertEqual(self.db.execute("SELECT * FROM bar WHERE firstname IN (?)", ["baz", "qux"]), [{"firstname": "baz"}, {"firstname": "qux"}])
        self.db.execute("DELETE FROM bar")

        self.assertRaises(RuntimeError, self.db.execute, "INSERT INTO foo VALUES (?)")
        self.assertRaises(RuntimeError, self.db.execute, "INSERT INTO foo VALUES (?, ?)")
        self.assertRaises(RuntimeError, self.db.execute, "INSERT INTO foo VALUES (?, ?)", 'bar', 'baz', 'qux')
        self.assertRaises(RuntimeError, self.db.execute, "INSERT INTO foo VALUES (?, ?)", ('bar', 'baz', 'qux'))
        self.assertRaises(RuntimeError, self.db.execute, "INSERT INTO foo VALUES (?, ?)", ['bar', 'baz', 'qux'])
        self.assertRaises(RuntimeError, self.db.execute, "INSERT INTO foo VALUES (?, ?)", 'bar', baz='baz')

    def test_named(self):
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

        self.db.execute("CREATE TABLE bar (firstname STRING)")
        self.db.execute("INSERT INTO bar VALUES (:baz)", baz="baz")
        self.assertEqual(self.db.execute("SELECT * FROM bar"), [{"firstname": "baz"}])

        self.assertRaises(RuntimeError, self.db.execute, "INSERT INTO foo VALUES (:bar)")
        self.assertRaises(RuntimeError, self.db.execute, "INSERT INTO foo VALUES (:bar, :baz)")
        self.assertRaises(RuntimeError, self.db.execute, "INSERT INTO foo VALUES (:bar, :baz)", bar='bar', baz='baz', qux='qux')
        self.assertRaises(RuntimeError, self.db.execute, "INSERT INTO foo VALUES (:bar, :baz)", 'baz', bar='bar')


    def test_numeric(self):
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
        self.db.execute("DELETE FROM foo")

        self.db.execute("INSERT INTO foo VALUES (:1,:2)", "bar", "baz")
        self.assertEqual(self.db.execute("SELECT * FROM foo"), [{"firstname": "bar", "lastname": "baz"}])
        self.db.execute("DELETE FROM foo")

        self.db.execute("CREATE TABLE bar (firstname STRING)")
        self.db.execute("INSERT INTO bar VALUES (:1)", "baz")
        self.assertEqual(self.db.execute("SELECT * FROM bar"), [{"firstname": "baz"}])

        self.assertRaises(RuntimeError, self.db.execute, "INSERT INTO foo VALUES (:1)")
        self.assertRaises(RuntimeError, self.db.execute, "INSERT INTO foo VALUES (:1, :2)")
        self.assertRaises(RuntimeError, self.db.execute, "INSERT INTO foo VALUES (:1, :2)", 'bar', 'baz', 'qux')
        self.assertRaises(RuntimeError, self.db.execute, "INSERT INTO foo VALUES (:1, :2)", 'bar', baz='baz')

    def test_cte(self):
        self.assertEqual(self.db.execute("WITH foo AS ( SELECT 1 AS bar ) SELECT bar FROM foo"), [{"bar": 1}])


if __name__ == "__main__":
    suite = unittest.TestSuite([
        unittest.TestLoader().loadTestsFromTestCase(SQLiteTests),
        #unittest.TestLoader().loadTestsFromTestCase(MySQLTests),
        unittest.TestLoader().loadTestsFromTestCase(PostgresTests)
    ])

    logging.getLogger("cs50").disabled = True
    sys.exit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
