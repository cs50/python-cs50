import contextlib
import io
import sys
import unittest

import cs50

class PythonTests(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        print("\nPython tests")

    @contextlib.contextmanager
    def replace_stdin(self):
        old = sys.stdin
        try:
            with io.StringIO() as stdin_s:
                sys.stdin = stdin_s
                sys.stdin.buffer = sys.stdin
                yield sys.stdin
        finally:
            sys.stdin = old

    def test_eprint(self):
        try:
            cs50.eprint("test")
        except (RuntimeError, AttributeError):
            pass
        
    def test_get_char(self):
        try:
            cs50.get_char("char: ")
        except (RuntimeError, AttributeError):
            pass

    def test_get_float_int(self):
        f = io.StringIO()
        with self.replace_stdin(), contextlib.redirect_stdout(f):
            sys.stdin.write("5\n")
            sys.stdin.seek(0)
            self.assertEqual(5.0, cs50.get_float("number: "))
            self.assertEqual(1, f.getvalue().count("number: "))

    def test_get_float_float(self):
        f = io.StringIO()
        with self.replace_stdin(), contextlib.redirect_stdout(f):
            sys.stdin.write("5.0\n")
            sys.stdin.seek(0)
            self.assertEqual(5.0, cs50.get_float("number: "))
            self.assertEqual(1, f.getvalue().count("number: "))

    def test_get_float_str(self):
        f = io.StringIO()
        with self.replace_stdin(), contextlib.redirect_stdout(f):
            sys.stdin.write("foo\nfoo\n")
            sys.stdin.seek(0)
            self.assertEqual(None, cs50.get_float("number: "))
            self.assertEqual(3, f.getvalue().count("number: "))

    def test_get_int_int(self):
        f = io.StringIO()
        with self.replace_stdin(), contextlib.redirect_stdout(f):
            sys.stdin.write("5\n")
            sys.stdin.seek(0)
            self.assertEqual(5, cs50.get_int("number: "))
            self.assertEqual(1, f.getvalue().count("number: "))

    def test_get_int_float(self):
        f = io.StringIO()
        with self.replace_stdin(), contextlib.redirect_stdout(f):
            sys.stdin.write("5.0\n")
            sys.stdin.seek(0)
            self.assertEqual(None, cs50.get_int("number: "))
            self.assertEqual(2, f.getvalue().count("number: "))

    def test_get_int_str(self):
        f = io.StringIO()
        with self.replace_stdin(), contextlib.redirect_stdout(f):
            sys.stdin.write("foo\nfoo\n")
            sys.stdin.seek(0)
            self.assertEqual(None, cs50.get_int("number: "))
            self.assertEqual(3, f.getvalue().count("number: "))

    def test_get_str(self):
        f = io.StringIO()
        with self.replace_stdin(), contextlib.redirect_stdout(f):
            sys.stdin.write("foo bar\n")
            sys.stdin.seek(0)
            self.assertEqual("foo bar", cs50.get_string("string: "))
            self.assertEqual(1, f.getvalue().count("string: "))

    def test_get_str_none(self):
        f = io.StringIO()
        with self.replace_stdin(), contextlib.redirect_stdout(f):
            sys.stdin.write("")
            sys.stdin.seek(0)
            self.assertEqual(None, cs50.get_string("string: "))
            self.assertEqual(1, f.getvalue().count("string: "))


if __name__ == "__main__":
    suite = unittest.TestSuite([
        unittest.TestLoader().loadTestsFromTestCase(CS50Tests)
    ])

    sys.exit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
