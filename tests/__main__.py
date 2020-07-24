import logging
import unittest
import sys

from .sql_tests import MySQLTests, PostgresTests, SQLiteTests
from .flask_tests import FlaskTests
from .python_tests import PythonTests

sys.path.insert(0, "../src")

# It's critical that SQLiteTests run before FlaskTests, because
# the latter turns off loggers so as to not clutter the screen
suite = unittest.TestSuite([
    unittest.TestLoader().loadTestsFromTestCase(SQLiteTests),
    unittest.TestLoader().loadTestsFromTestCase(MySQLTests),
    unittest.TestLoader().loadTestsFromTestCase(PostgresTests),
    unittest.TestLoader().loadTestsFromTestCase(FlaskTests),
    unittest.TestLoader().loadTestsFromTestCase(PythonTests)
])
result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(bool(result.errors or result.failures))
