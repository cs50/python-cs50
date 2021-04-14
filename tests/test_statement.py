import unittest

from unittest.mock import patch

from cs50._statement import Statement
from cs50._sql_sanitizer import SQLSanitizer


@patch.object(SQLSanitizer, "escape", return_value="test")
class TestStatement(unittest.TestCase):
    # TODO assert correct exception messages
    def test_mutex_args_and_kwargs(self, MockSQLSanitizer):
        with self.assertRaises(RuntimeError):
            Statement(MockSQLSanitizer(), "SELECT * FROM test WHERE id = ? AND val = :val", 1, val="test")

        with self.assertRaises(RuntimeError):
            Statement(MockSQLSanitizer(), "SELECT * FROM test", "test", 1, 2, foo="foo", bar="bar")

    @patch.object(Statement, "_escape_verbatim_colons")
    def test_valid_qmark_count(self, MockSQLSanitizer, *_):
        Statement(MockSQLSanitizer(), "SELECT * FROM test WHERE id = ?", 1)
        Statement(MockSQLSanitizer(), "SELECT * FROM test WHERE id = ? and val = ?", 1, 'test')
        Statement(MockSQLSanitizer(),
                  "INSERT INTO test (id, val, is_valid) VALUES (?, ?, ?)", 1, 'test', True)

    @patch.object(Statement, "_escape_verbatim_colons")
    def test_invalid_qmark_count(self, MockSQLSanitizer, *_):
        def assert_invalid_count(sql, *args):
            with self.assertRaises(RuntimeError, msg=f"{sql} {str(args)}"):
                Statement(MockSQLSanitizer(), sql, *args)

        statements = [
            ("SELECT * FROM test WHERE id = ?", ()),
            ("SELECT * FROM test WHERE id = ?", (1, "test")),
            ("SELECT * FROM test WHERE id = ? AND val = ?", (1,)),
            ("SELECT * FROM test WHERE id = ? AND val = ?", ()),
            ("SELECT * FROM test WHERE id = ? AND val = ?", (1, "test", True)),
        ]

        for sql, args in statements:
            assert_invalid_count(sql, *args)

    @patch.object(Statement, "_escape_verbatim_colons")
    def test_valid_format_count(self, MockSQLSanitizer, *_):
        Statement(MockSQLSanitizer(), "SELECT * FROM test WHERE id = %s", 1)
        Statement(MockSQLSanitizer(), "SELECT * FROM test WHERE id = %s and val = %s", 1, 'test')
        Statement(MockSQLSanitizer(),
                  "INSERT INTO test (id, val, is_valid) VALUES (%s, %s, %s)", 1, 'test', True)

    @patch.object(Statement, "_escape_verbatim_colons")
    def test_invalid_format_count(self, MockSQLSanitizer, *_):
        def assert_invalid_count(sql, *args):
            with self.assertRaises(RuntimeError, msg=f"{sql} {str(args)}"):
                Statement(MockSQLSanitizer(), sql, *args)

        statements = [
            ("SELECT * FROM test WHERE id = %s", ()),
            ("SELECT * FROM test WHERE id = %s", (1, "test")),
            ("SELECT * FROM test WHERE id = %s AND val = ?", (1,)),
            ("SELECT * FROM test WHERE id = %s AND val = ?", ()),
            ("SELECT * FROM test WHERE id = %s AND val = ?", (1, "test", True)),
        ]

        for sql, args in statements:
            assert_invalid_count(sql, *args)

    @patch.object(Statement, "_escape_verbatim_colons")
    def test_missing_numeric(self, MockSQLSanitizer, *_):
        def assert_missing_numeric(sql, *args):
            with self.assertRaises(RuntimeError, msg=f"{sql} {str(args)}"):
                Statement(MockSQLSanitizer(), sql, *args)

        statements = [
            ("SELECT * FROM test WHERE id = :1", ()),
            ("SELECT * FROM test WHERE id = :1 AND val = :2", ()),
            ("SELECT * FROM test WHERE id = :1 AND val = :2", (1,)),
            ("SELECT * FROM test WHERE id = :1 AND val = :2 AND is_valid = :3", ()),
            ("SELECT * FROM test WHERE id = :1 AND val = :2 AND is_valid = :3", (1,)),
            ("SELECT * FROM test WHERE id = :1 AND val = :2 AND is_valid = :3", (1, "test")),
        ]

        for sql, args in statements:
            assert_missing_numeric(sql, *args)

    @patch.object(Statement, "_escape_verbatim_colons")
    def test_unused_numeric(self, MockSQLSanitizer, *_):
        def assert_unused_numeric(sql, *args):
            with self.assertRaises(RuntimeError, msg=f"{sql} {str(args)}"):
                Statement(MockSQLSanitizer(), sql, *args)

        statements = [
            ("SELECT * FROM test WHERE id = :1", (1, "test")),
            ("SELECT * FROM test WHERE id = :1", (1, "test", True)),
            ("SELECT * FROM test WHERE id = :1 AND val = :2", (1, "test", True)),
        ]

        for sql, args in statements:
            assert_unused_numeric(sql, *args)

    @patch.object(Statement, "_escape_verbatim_colons")
    def test_missing_named(self, MockSQLSanitizer, *_):
        def assert_missing_named(sql, **kwargs):
            with self.assertRaises(RuntimeError, msg=f"{sql} {str(kwargs)}"):
                Statement(MockSQLSanitizer(), sql, **kwargs)

        statements = [
            ("SELECT * FROM test WHERE id = :id", {}),
            ("SELECT * FROM test WHERE id = :id AND val = :val", {}),
            ("SELECT * FROM test WHERE id = :id AND val = :val", {"id": 1}),
            ("SELECT * FROM test WHERE id = :id AND val = :val AND is_valid = :is_valid", {}),
            ("SELECT * FROM test WHERE id = :id AND val = :val AND is_valid = :is_valid",
             {"id": 1}),
            ("SELECT * FROM test WHERE id = :id AND val = :val AND is_valid = :is_valid",
             {"id": 1, "val": "test"}),
        ]

        for sql, kwargs in statements:
            assert_missing_named(sql, **kwargs)

    @patch.object(Statement, "_escape_verbatim_colons")
    def test_unused_named(self, MockSQLSanitizer, *_):
        def assert_unused_named(sql, **kwargs):
            with self.assertRaises(RuntimeError, msg=f"{sql} {str(kwargs)}"):
                Statement(MockSQLSanitizer(), sql, **kwargs)

        statements = [
            ("SELECT * FROM test WHERE id = :id", {"id": 1, "val": "test"}),
            ("SELECT * FROM test WHERE id = :id", {"id": 1, "val": "test", "is_valid": True}),
            ("SELECT * FROM test WHERE id = :id AND val = :val",
             {"id": 1, "val": "test", "is_valid": True}),
        ]

        for sql, kwargs in statements:
            assert_unused_named(sql, **kwargs)

    @patch.object(Statement, "_escape_verbatim_colons")
    def test_missing_pyformat(self, MockSQLSanitizer, *_):
        def assert_missing_pyformat(sql, **kwargs):
            with self.assertRaises(RuntimeError, msg=f"{sql} {str(kwargs)}"):
                Statement(MockSQLSanitizer(), sql, **kwargs)

        statements = [
            ("SELECT * FROM test WHERE id = %(id)s", {}),
            ("SELECT * FROM test WHERE id = %(id)s AND val = %(val)s", {}),
            ("SELECT * FROM test WHERE id = %(id)s AND val = %(val)s", {"id": 1}),
            ("SELECT * FROM test WHERE id = %(id)s AND val = %(val)s AND is_valid = %(is_valid)s", {}),
            ("SELECT * FROM test WHERE id = %(id)s AND val = %(val)s AND is_valid = %(is_valid)s",
             {"id": 1}),
            ("SELECT * FROM test WHERE id = %(id)s AND val = %(val)s AND is_valid = %(is_valid)s",
             {"id": 1, "val": "test"}),
        ]

        for sql, kwargs in statements:
            assert_missing_pyformat(sql, **kwargs)

    @patch.object(Statement, "_escape_verbatim_colons")
    def test_unused_pyformat(self, MockSQLSanitizer, *_):
        def assert_unused_pyformat(sql, **kwargs):
            with self.assertRaises(RuntimeError, msg=f"{sql} {str(kwargs)}"):
                Statement(MockSQLSanitizer(), sql, **kwargs)

        statements = [
            ("SELECT * FROM test WHERE id = %(id)s", {"id": 1, "val": "test"}),
            ("SELECT * FROM test WHERE id = %(id)s", {"id": 1, "val": "test", "is_valid": True}),
            ("SELECT * FROM test WHERE id = %(id)s AND val = %(val)s",
             {"id": 1, "val": "test", "is_valid": True}),
        ]

        for sql, kwargs in statements:
            assert_unused_pyformat(sql, **kwargs)

    def test_multiple_statements(self, MockSQLSanitizer):
        def assert_raises_runtimeerror(sql):
            with self.assertRaises(RuntimeError):
                Statement(MockSQLSanitizer(), sql)

        statements = [
            "SELECT 1; SELECT 2;",
            "SELECT 1; SELECT 2",
            "SELECT 1; SELECT 2; SELECT 3",
            "SELECT 1; SELECT 2; SELECT 3;",
            "SELECT 1;SELECT 2",
            "select 1; select 2",
            "select 1;select 2",
            "DELETE FROM test; SELECT * FROM test",
        ]

        for sql in statements:
            assert_raises_runtimeerror(sql)

    def test_is_delete(self, MockSQLSanitizer):
        self.assertTrue(Statement(MockSQLSanitizer(), "DELETE FROM test").is_delete())
        self.assertTrue(Statement(MockSQLSanitizer(), "delete FROM test").is_delete())
        self.assertFalse(Statement(MockSQLSanitizer(), "SELECT * FROM test").is_delete())
        self.assertFalse(Statement(MockSQLSanitizer(),
                         "INSERT INTO test (id, val) VALUES (1, 'test')").is_delete())

    def test_is_insert(self, MockSQLSanitizer):
        self.assertTrue(Statement(MockSQLSanitizer(),
                        "INSERT INTO test (id, val) VALUES (1, 'test')").is_insert())
        self.assertTrue(Statement(MockSQLSanitizer(),
                        "insert INTO test (id, val) VALUES (1, 'test')").is_insert())
        self.assertFalse(Statement(MockSQLSanitizer(), "SELECT * FROM test").is_insert())
        self.assertFalse(Statement(MockSQLSanitizer(), "DELETE FROM test").is_insert())

    def test_is_select(self, MockSQLSanitizer):
        self.assertTrue(Statement(MockSQLSanitizer(), "SELECT * FROM test").is_select())
        self.assertTrue(Statement(MockSQLSanitizer(), "select * FROM test").is_select())
        self.assertFalse(Statement(MockSQLSanitizer(), "DELETE FROM test").is_select())
        self.assertFalse(Statement(MockSQLSanitizer(),
                         "INSERT INTO test (id, val) VALUES (1, 'test')").is_select())

    def test_is_update(self, MockSQLSanitizer):
        self.assertTrue(Statement(MockSQLSanitizer(), "UPDATE test SET id = 2").is_update())
        self.assertTrue(Statement(MockSQLSanitizer(), "update test SET id = 2").is_update())
        self.assertFalse(Statement(MockSQLSanitizer(), "SELECT * FROM test").is_update())
        self.assertFalse(Statement(MockSQLSanitizer(),
                         "INSERT INTO test (id, val) VALUES (1, 'test')").is_update())

    def test_is_transaction_start(self, MockSQLSanitizer):
        self.assertTrue(Statement(MockSQLSanitizer(), "START TRANSACTION").is_transaction_start())
        self.assertTrue(Statement(MockSQLSanitizer(), "start TRANSACTION").is_transaction_start())
        self.assertTrue(Statement(MockSQLSanitizer(), "BEGIN").is_transaction_start())
        self.assertTrue(Statement(MockSQLSanitizer(), "begin").is_transaction_start())
        self.assertFalse(Statement(MockSQLSanitizer(), "SELECT * FROM test").is_transaction_start())
        self.assertFalse(Statement(MockSQLSanitizer(), "DELETE FROM test").is_transaction_start())

    def test_is_transaction_end(self, MockSQLSanitizer):
        self.assertTrue(Statement(MockSQLSanitizer(), "COMMIT").is_transaction_end())
        self.assertTrue(Statement(MockSQLSanitizer(), "commit").is_transaction_end())
        self.assertTrue(Statement(MockSQLSanitizer(), "ROLLBACK").is_transaction_end())
        self.assertTrue(Statement(MockSQLSanitizer(), "rollback").is_transaction_end())
        self.assertFalse(Statement(MockSQLSanitizer(), "SELECT * FROM test").is_transaction_end())
        self.assertFalse(Statement(MockSQLSanitizer(), "DELETE FROM test").is_transaction_end())
