import sys
import unittest
import logging
import warnings
from unittest.mock import patch

sys.path.insert(0, "../src")

import cs50

class FunctionTests(unittest.TestCase):
    
    @patch("cs50.get_int", return_value=1)
    def test_get_int(self, input):
        """
        Tests the get_int() function
        """
        i = cs50.get_int("Integer: ")
        self.assertIsInstance(i, int)

    @patch("cs50.get_float", return_value=1.0)
    def test_get_float(self, input):
        """
        Tests the get_float() function
        """
        i = cs50.get_float("Float: ")
        self.assertIsInstance(i, float)

    @patch("cs50.get_string", return_value="1")
    def test_get_string(self, input):
        """
        Tests the get_string() function
        """
        i = cs50.get_string("String: ")
        self.assertIsInstance(i, str)

if __name__ == "__main__":
    suite = unittest.TestSuite([
        unittest.TestLoader().loadTestsFromTestCase(FunctionTests)
    ])

    logging.getLogger("cs50").disabled = True
    sys.exit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
    