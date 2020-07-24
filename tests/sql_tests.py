import contextlib
import logging
import sys
import unittest
import warnings

sys.path.insert(0, "src")

from cs50.sql import SQL


class SQLTests(unittest.TestCase):

    def setUp(self):
        if self.__class__.__name__ == "SQLTests":
            self.skipTest("This is a base class; no tests.")

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

    def test_autocommit(self):
        self.assertEqual(self.db.execute("INSERT INTO cs50(val) VALUES('foo')"), 1)
        self.assertEqual(self.db.execute("INSERT INTO cs50(val) VALUES('bar')"), 2)

        # Load a new database instance to confirm the INSERTs were committed
        db2 = SQL(self.db_url)
        self.assertEqual(db2.execute("DELETE FROM cs50 WHERE id < 3"), 2)

    def test_commit_no_transaction(self):
        with self.assertRaises(RuntimeError):
            self.db.execute("COMMIT")
        with self.assertRaises(RuntimeError):
            self.db.execute("ROLLBACK")

    def test_commit(self):
        self.db.execute("BEGIN")
        self.db.execute("INSERT INTO cs50 (val) VALUES('foo')")
        self.db.execute("COMMIT")

        # Load a new database instance to confirm the INSERT was committed
        db2 = SQL(self.db_url)
        self.assertEqual(db2.execute("SELECT val FROM cs50"), [{"val": "foo"}])

    def test_double_begin(self):
        self.db.execute("BEGIN")
        with self.assertRaises(RuntimeError):
            self.db.execute("BEGIN")
        self.db.execute("ROLLBACK")

    def test_rollback(self):
        self.db.execute("BEGIN")
        self.db.execute("INSERT INTO cs50 (val) VALUES('foo')")
        self.db.execute("INSERT INTO cs50 (val) VALUES('bar')")
        self.db.execute("ROLLBACK")
        self.assertEqual(self.db.execute("SELECT val FROM cs50"), [])

    def test_savepoint(self):
        self.db.execute("BEGIN")
        self.db.execute("INSERT INTO cs50 (val) VALUES('foo')")
        self.db.execute("SAVEPOINT sp1")
        self.db.execute("INSERT INTO cs50 (val) VALUES('bar')")
        self.assertEqual(self.db.execute("SELECT val FROM cs50"), [{"val": "foo"}, {"val": "bar"}])
        self.db.execute("ROLLBACK TO sp1")
        self.assertEqual(self.db.execute("SELECT val FROM cs50"), [{"val": "foo"}])
        self.db.execute("ROLLBACK")
        self.assertEqual(self.db.execute("SELECT val FROM cs50"), [])

    def tearDown(self):
        self.db.execute("DROP TABLE IF EXISTS cs50")
        self.db.execute("DROP TABLE IF EXISTS foo")
        self.db.execute("DROP TABLE IF EXISTS bar")

    @classmethod
    def tearDownClass(self):
        if not hasattr(self, "db"):
            return

        try:
            self.db.execute("DROP TABLE IF EXISTS cs50")
        except Warning as e:
            # suppress "unknown table"
            if not str(e).startswith("(1051"):
                raise e

class MySQLTests(SQLTests):
    @classmethod
    def setUpClass(self):
        self.db_url = "mysql://root@localhost/test"
        self.db = SQL(self.db_url)
        print("\nMySQL tests")

    def setUp(self):
        self.db.execute("CREATE TABLE cs50 (id INTEGER NOT NULL AUTO_INCREMENT, val VARCHAR(16), bin BLOB, PRIMARY KEY (id))")

class PostgresTests(SQLTests):
    @classmethod
    def setUpClass(self):
        self.db_url = "postgresql://postgres@localhost/test"
        self.db = SQL(self.db_url)
        print("\nPOSTGRES tests")

    def setUp(self):
        self.db.execute("CREATE TABLE cs50 (id SERIAL PRIMARY KEY, val VARCHAR(16), bin BYTEA)")

    def test_cte(self):
        self.assertEqual(self.db.execute("WITH foo AS ( SELECT 1 AS bar ) SELECT bar FROM foo"), [{"bar": 1}])

class SQLiteTests(SQLTests):
    @classmethod
    def setUpClass(self):
        open("test.db", "w").close()
        self.db_url = "sqlite:///test.db"
        self.db = SQL(self.db_url)
        print("\nSQLite tests")

    def setUp(self):
        self.db.execute("CREATE TABLE IF NOT EXISTS cs50(id INTEGER PRIMARY KEY, val TEXT, bin BLOB)")

    @classmethod
    @contextlib.contextmanager
    def assertNoLog(self, name, level="INFO", specifically=None):
        with self.assertLogs(name, level=level) as cm:
            yield

        if cm.output[:-1]:
            # If we're only checking for the absence of a particular message
            if specifically:
                if True not in map(lambda e: specifically in e, cm.output):
                    yield
                else:
                    raise AssertionError("logs detected:", cm.output)
            else:
                raise AssertionError("logs detected:", cm.output)

    def test_parameter_warnings_deletes(self):
        logging.getLogger("cs50").disabled = False

        deletes = [
            ["?", "", ["test"]],
            ["test", "WHERE ?=3", ["id"]]
        ]

        for dlt in deletes:
            with self.assertLogs("cs50", level="DEBUG") as cm:
                command = f"DELETE FROM {dlt[0]} {dlt[1]}"
                
                # We don't care about the query results, just about the logs
                try:
                    self.db.execute(command, *dlt[2])
                except RuntimeError:
                    pass

                self.assertTrue(True in map(lambda o: "This may cause errors" in o, cm.output))

        logging.getLogger("cs50").disabled = True

    def test_parameter_warnings_inserts(self):
        logging.getLogger("cs50").disabled = False
        
        inserts = [
            ["test", "(id, ?)", "VALUES (3, ?)", ["name", "foo"]],
            ["test", "(?, ?)", "VALUES (3, 'foo')", ["id", "name"]],
            ["?", "(id, name)", "VALUES (3, 'foo')", ["test"]],
            ["?", "(?, ?)", "VALUES (3, 'foo')", ["test", "id", "name"]],
            ["?", "SELECT id FROM test", "", ["test3"]],
            ["test3", "SELECT ? FROM test", "", ["id"]]
        ]

        for ins in inserts:
            with self.assertLogs("cs50", level="DEBUG") as cm:
                command = f"INSERT INTO {ins[0]} {ins[1]} {ins[2]}"
                
                try:
                    self.db.execute(command, *ins[3])
                except RuntimeError:
                    pass

            self.assertTrue(True in map(lambda o: "This may cause errors" in o, cm.output))

        logging.getLogger("cs50").disabled = True

    def test_parameter_warnings_misc(self):
        logging.getLogger("cs50").disabled = False
        
        queries = [
            ["CREATE DATABASE ?", ["foo"]],
            ["DROP DATABASE ?", ["foo"]],
            ["CREATE TABLE ? (id INTEGER)", ["foo"]],
            ["CREATE TABLE foo (? INTEGER)", ["id"]],
            ["DROP TABLE ?", ["foo"]],
            ["ALTER TABLE ? ADD num INTEGER", ["foo"]],
            ["ALTER TABLE foo ADD ? INTEGER", ["num"]],
            ["ALTER TABLE foo DROP COLUMN ?", ["num"]]
        ]

        for query in queries:
            with self.assertLogs("cs50", level="DEBUG") as cm:
                try:
                    self.db.execute(query[0], *query[1])
                except RuntimeError:
                    pass

            self.assertTrue(True in map(lambda o: "This may cause errors" in o, cm.output))

        logging.getLogger("cs50").disabled = True

    def test_parameter_warnings_selects(self):
        logging.getLogger("cs50").disabled = False
        
        selects = [
            # Base tests
            ["?", "test", "", ["name"]],
            ["id", "?", "", ["test"]],
            ["?, ?", "test", "", ["id", "name"]],
            ["id, ?", "test", "", ["name"]],
            
            # Aggregation functions
            ["COUNT(?)", "test", "", ["id"]],
            ["AVG(?)", "test", "", ["id"]],
            ["SUM(?)", "test", "", ["id"]],
            ["MIN(?)", "test", "", ["id"]],
            ["MAX(?)", "test", "", ["id"]],

            # Comparisons
            ["name", "test", "WHERE ? > 4", ["id"]],
            ["name", "test", "WHERE ? >= 4", ["id"]],
            ["name", "test", "WHERE ? = 4", ["id"]],
            ["name", "test", "WHERE ? <= 4", ["id"]],
            ["name", "test", "WHERE ? < 4", ["id"]],
            ["name", "test", "WHERE NOT ? > 4", ["id"]],
            ["id", "test", "WHERE ? IS NULL", ["name"]],
            ["id", "test", "WHERE ? IS NOT NULL", ["name"]],
            ["name", "test", "WHERE ? BETWEEN 3 AND 7", ["id"]],
            ["id", "test", "WHERE ? LIKE '%foo'", ["name"]],
            ["name", "test", "WHERE ? IN (SELECT id FROM test)", ["id"]],

            # AND and OR
            ["name", "test", "WHERE id < 4 AND ? > 1", ["id"]],
            ["name", "test", "WHERE id < 4 OR ? > 7", ["id"]],

            # ORDER BY and GROUP BY
            ["name", "test", "ORDER BY ?", ["id"]],
            ["name", "test", "ORDER BY ?, ?", ["id", "name"]],
            ["name", "test", "ORDER BY id, ?", ["name"]],
            ["name", "test", "ORDER BY ? DESC", ["id"]],
            ["name", "test", "GROUP BY ?", ["id"]],
            ["name", "test", "GROUP BY name, ?", ["id"]],

            # Other odds and ends
            ["DISTINCT ?", "test", "", ["id"]],
            ["id AS ?", "test", "", ["new_id"]],
            ["name", "test", "WHERE id IN (SELECT ? FROM test2)", ["id"]],
            ["INTO ?", "test", "", ["test3"]],

            # Joins
            ["test.id, test2.name", "test", "INNER JOIN ? ON test2.id=test.id", ["test"]],
            ["test.id, test2.name", "test", "INNER JOIN test ON ?=test.id", ["test2.id"]],
            ["test.id, test2.name", "test", "INNER JOIN test ON test2.id=?", ["test.id"]],
            ["test.id, test2.name", "test", "LEFT JOIN ? ON test2.id=test.id", ["test2"]],
            ["test.id, test2.name", "test", "RIGHT JOIN ? ON test2.id=test.id", ["test2"]],
            ["test.id, test2.name", "test", "FULL OUTER JOIN ? ON test2.id=test.id", ["test2"]]
        ]

        for sel in selects:
            with self.assertLogs("cs50", level="DEBUG") as cm:
                command = f"SELECT {sel[0]} FROM {sel[1]} {sel[2]}"
                    
                try:
                    self.db.execute(command, *sel[3])
                except RuntimeError:
                    pass

            self.assertTrue(True in map(lambda o: "This may cause errors" in o, cm.output))
                
        logging.getLogger("cs50").disabled = True

    def test_parameter_warnings_updates(self):
        logging.getLogger("cs50").disabled = False
        
        updates = [
            ["?", "id=3", "WHERE name='foo'", ["test"]],
            ["test", "?=4", "WHERE name='foo'", ["id"]],
            ["test", "id=3", "WHERE ?=4", ["id"]],
            ["test", "id=3, ?='bar'", "WHERE name='foo'", ["name"]]
        ]

        for upd in updates:
            with self.assertLogs("cs50", level="DEBUG") as cm:
                command = f"UPDATE {upd[0]} SET {upd[1]} {upd[2]}"
                
                try:
                    self.db.execute(command, *upd[3])
                except RuntimeError:
                    pass

            self.assertTrue(True in map(lambda o: "This may cause errors" in o, cm.output))

        logging.getLogger("cs50").disabled = True

    def test_parameter_warnings_valid(self):
        logging.getLogger("cs50").disabled = False
        
        # None of these should give warnings about parameters
        queries = [
            ["SELECT * FROM test", []],
            ["SELECT * FROM test WHERE id=?", [5]],
            ["SELECT * FROM test WHERE id IN (SELECT id FROM test2)", []],
            ["SELECT * FROM test WHERE id < 6 AND name LIKE ?", ["%foo"]],
            ["SELECT * FROM test ORDER BY name", []],
            ["SELECT * FROM test GROUP BY name", []],
            ["SELECT test.id, test2.name FROM test INNER JOIN ON test.id=test2.id", []],
            ["INSERT INTO test (id, name) VALUES (?, ?)", [3, "foo"]],
            ["INSERT INTO test SELECT id, name FROM test2", []],
            ["UPDATE test SET name=? WHERE id=?", ["bar", 3]],
            ["UPDATE test SET name=? WHERE id=? AND NOT name=?", ["foo", 3, "bar"]],
            ["DELETE FROM test WHERE id=? AND NOT name=?", [3, "foo"]],
            ["CREATE TABLE test3 (id INTEGER)", []],
            ["DROP TABLE test3", []],
            ["CREATE DATABASE test4", []],
            ["DROP DATABASE test4", []],
            ["ALTER TABLE test ADD num INTEGER", []],
            ["ALTER TABLE test DROP COLUMN num", []]
        ]

        for query in queries:
            with self.assertNoLog("cs50", level="DEBUG", specifically="This may cause errors"):
                try:
                    self.db.execute(query[0], *query[1])
                except RuntimeError:
                    pass

        logging.getLogger("cs50").disabled = True

    def test_lastrowid(self):
        self.db.execute("CREATE TABLE foo(id INTEGER PRIMARY KEY AUTOINCREMENT, firstname TEXT, lastname TEXT)")
        self.assertEqual(self.db.execute("INSERT INTO foo (firstname, lastname) VALUES('firstname', 'lastname')"), 1)
        self.assertRaises(RuntimeError, self.db.execute, "INSERT INTO foo (id, firstname, lastname) VALUES(1, 'firstname', 'lastname')")
        self.assertEqual(self.db.execute("INSERT OR IGNORE INTO foo (id, firstname, lastname) VALUES(1, 'firstname', 'lastname')"), None)

    def test_integrity_constraints(self):
        self.db.execute("CREATE TABLE foo(id INTEGER PRIMARY KEY)")
        self.assertEqual(self.db.execute("INSERT INTO foo VALUES(1)"), 1)
        self.assertRaises(RuntimeError, self.db.execute, "INSERT INTO foo VALUES(1)")

    def test_foreign_key_support(self):
        self.db.execute("CREATE TABLE foo(id INTEGER PRIMARY KEY)")
        self.db.execute("CREATE TABLE bar(foo_id INTEGER, FOREIGN KEY (foo_id) REFERENCES foo(id))")
        self.assertRaises(RuntimeError, self.db.execute, "INSERT INTO bar VALUES(50)")

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
        unittest.TestLoader().loadTestsFromTestCase(SQLiteTests)
        #unittest.TestLoader().loadTestsFromTestCase(MySQLTests),
        #unittest.TestLoader().loadTestsFromTestCase(PostgresTests)
    ])

    logging.getLogger("cs50").disabled = True
    sys.exit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
