import unittest

from unittest.mock import patch

from cs50._statement import Statement
from cs50._sql_sanitizer import SQLSanitizer

class TestStatement(unittest.TestCase):
    # TODO assert correct exception messages
    def test_mutex_args_and_kwargs(self):
        with self.assertRaises(RuntimeError):
            Statement("", "", "test", foo="foo")

        with self.assertRaises(RuntimeError):
            Statement("", "", "test", 1, 2, foo="foo", bar="bar")

    @patch.object(SQLSanitizer, "escape", return_value="test")
    @patch.object(Statement, "_escape_verbatim_colons")
    def test_valid_qmark_count(self, *_):
        Statement("", "SELECT * FROM test WHERE id = ?", 1)
        Statement("", "SELECT * FROM test WHERE id = ? and val = ?", 1, 'test')
        Statement("", "INSERT INTO test (id, val, is_valid) VALUES (?, ?, ?)", 1, 'test', True)

    @patch.object(SQLSanitizer, "escape", return_value="test")
    @patch.object(Statement, "_escape_verbatim_colons")
    def test_invalid_qmark_count(self, *_):
        def assert_invalid_count(sql, *args):
            with self.assertRaises(RuntimeError, msg=f"{sql} {str(args)}"):
                Statement("", sql, *args)

        statements = [
            ("SELECT * FROM test WHERE id = ?", ()),
            ("SELECT * FROM test WHERE id = ?", (1, "test")),
            ("SELECT * FROM test WHERE id = ? AND val = ?", (1,)),
            ("SELECT * FROM test WHERE id = ? AND val = ?", ()),
            ("SELECT * FROM test WHERE id = ? AND val = ?", (1, "test", True)),
        ]

        for sql, args in statements:
            assert_invalid_count(sql, *args)


    @patch.object(SQLSanitizer, "escape", return_value="test")
    @patch.object(Statement, "_escape_verbatim_colons")
    def test_valid_format_count(self, *_):
        Statement("", "SELECT * FROM test WHERE id = %s", 1)
        Statement("", "SELECT * FROM test WHERE id = %s and val = %s", 1, 'test')
        Statement("", "INSERT INTO test (id, val, is_valid) VALUES (%s, %s, %s)", 1, 'test', True)

    @patch.object(SQLSanitizer, "escape", return_value="test")
    @patch.object(Statement, "_escape_verbatim_colons")
    def test_invalid_format_count(self, *_):
        def assert_invalid_count(sql, *args):
            with self.assertRaises(RuntimeError, msg=f"{sql} {str(args)}"):
                Statement("", sql, *args)

        statements = [
            ("SELECT * FROM test WHERE id = %s", ()),
            ("SELECT * FROM test WHERE id = %s", (1, "test")),
            ("SELECT * FROM test WHERE id = %s AND val = ?", (1,)),
            ("SELECT * FROM test WHERE id = %s AND val = ?", ()),
            ("SELECT * FROM test WHERE id = %s AND val = ?", (1, "test", True)),
        ]

        for sql, args in statements:
            assert_invalid_count(sql, *args)

    @patch.object(SQLSanitizer, "escape", return_value="test")
    @patch.object(Statement, "_escape_verbatim_colons")
    def test_missing_numeric(self, *_):
        def assert_missing_numeric(sql, *args):
            with self.assertRaises(RuntimeError, msg=f"{sql} {str(args)}"):
                Statement("", sql, *args)

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

    @patch.object(SQLSanitizer, "escape", return_value="test")
    @patch.object(Statement, "_escape_verbatim_colons")
    def test_unused_numeric(self, *_):
        def assert_unused_numeric(sql, *args):
            with self.assertRaises(RuntimeError, msg=f"{sql} {str(args)}"):
                Statement("", sql, *args)

        statements = [
            ("SELECT * FROM test WHERE id = :1", (1, "test")),
            ("SELECT * FROM test WHERE id = :1", (1, "test", True)),
            ("SELECT * FROM test WHERE id = :1 AND val = :2", (1, "test", True)),
        ]

        for sql, args in statements:
            assert_unused_numeric(sql, *args)

    @patch.object(SQLSanitizer, "escape", return_value="test")
    @patch.object(Statement, "_escape_verbatim_colons")
    def test_missing_named(self, *_):
        def assert_missing_named(sql, **kwargs):
            with self.assertRaises(RuntimeError, msg=f"{sql} {str(kwargs)}"):
                Statement("", sql, **kwargs)

        statements = [
            ("SELECT * FROM test WHERE id = :id", {}),
            ("SELECT * FROM test WHERE id = :id AND val = :val", {}),
            ("SELECT * FROM test WHERE id = :id AND val = :val", {"id": 1}),
            ("SELECT * FROM test WHERE id = :id AND val = :val AND is_valid = :is_valid", {}),
            ("SELECT * FROM test WHERE id = :id AND val = :val AND is_valid = :is_valid", {"id": 1}),
            ("SELECT * FROM test WHERE id = :id AND val = :val AND is_valid = :is_valid", {"id": 1, "val": "test"}),
        ]

        for sql, kwargs in statements:
            assert_missing_named(sql, **kwargs)

    @patch.object(SQLSanitizer, "escape", return_value="test")
    @patch.object(Statement, "_escape_verbatim_colons")
    def test_unused_named(self, *_):
        def assert_unused_named(sql, **kwargs):
            with self.assertRaises(RuntimeError, msg=f"{sql} {str(kwargs)}"):
                Statement("", sql, **kwargs)

        statements = [
            ("SELECT * FROM test WHERE id = :id", {"id": 1, "val": "test"}),
            ("SELECT * FROM test WHERE id = :id", {"id": 1, "val": "test", "is_valid": True}),
            ("SELECT * FROM test WHERE id = :id AND val = :val", {"id": 1, "val": "test", "is_valid": True}),
        ]

        for sql, kwargs in statements:
            assert_unused_named(sql, **kwargs)

    @patch.object(SQLSanitizer, "escape", return_value="test")
    @patch.object(Statement, "_escape_verbatim_colons")
    def test_missing_pyformat(self, *_):
        def assert_missing_pyformat(sql, **kwargs):
            with self.assertRaises(RuntimeError, msg=f"{sql} {str(kwargs)}"):
                Statement("", sql, **kwargs)

        statements = [
            ("SELECT * FROM test WHERE id = %(id)s", {}),
            ("SELECT * FROM test WHERE id = %(id)s AND val = %(val)s", {}),
            ("SELECT * FROM test WHERE id = %(id)s AND val = %(val)s", {"id": 1}),
            ("SELECT * FROM test WHERE id = %(id)s AND val = %(val)s AND is_valid = %(is_valid)s", {}),
            ("SELECT * FROM test WHERE id = %(id)s AND val = %(val)s AND is_valid = %(is_valid)s", {"id": 1}),
            ("SELECT * FROM test WHERE id = %(id)s AND val = %(val)s AND is_valid = %(is_valid)s", {"id": 1, "val": "test"}),
        ]

        for sql, kwargs in statements:
            assert_missing_pyformat(sql, **kwargs)

    @patch.object(SQLSanitizer, "escape", return_value="test")
    @patch.object(Statement, "_escape_verbatim_colons")
    def test_unused_pyformat(self, *_):
        def assert_unused_pyformat(sql, **kwargs):
            with self.assertRaises(RuntimeError, msg=f"{sql} {str(kwargs)}"):
                Statement("", sql, **kwargs)

        statements = [
            ("SELECT * FROM test WHERE id = %(id)s", {"id": 1, "val": "test"}),
            ("SELECT * FROM test WHERE id = %(id)s", {"id": 1, "val": "test", "is_valid": True}),
            ("SELECT * FROM test WHERE id = %(id)s AND val = %(val)s", {"id": 1, "val": "test", "is_valid": True}),
        ]

        for sql, kwargs in statements:
            assert_unused_pyformat(sql, **kwargs)

    def test_multiple_statements(self):
        def assert_raises_runtimeerror(sql):
            with self.assertRaises(RuntimeError):
                Statement("", sql)

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

    def test_get_operation_keyword(self):
        def test_raw_and_lowercase(sql, keyword):
            statement = Statement("", sql)
            self.assertEqual(statement.get_operation_keyword(), keyword)

            statement = Statement("", sql.lower())
            self.assertEqual(statement.get_operation_keyword(), keyword)


        statements = [
            ("SELECT * FROM test", "SELECT"),
            ("INSERT INTO test (id, val) VALUES (1, 'test')", "INSERT"),
            ("DELETE FROM test", "DELETE"),
            ("UPDATE test SET id = 2", "UPDATE"),
            ("START TRANSACTION", "START"),
            ("BEGIN", "BEGIN"),
            ("COMMIT", "COMMIT"),
            ("ROLLBACK", "ROLLBACK"),
        ]

        for sql, keyword in statements:
            test_raw_and_lowercase(sql, keyword)
