import sys
import unittest

from unittest.mock import patch

from cs50.cs50 import get_string, _get_int, _get_float


class TestCS50(unittest.TestCase):
    @patch("cs50.cs50._get_input", return_value="")
    def test_get_string_empty_input(self, mock_get_input):
        """Returns empty string when input is empty"""
        self.assertEqual(get_string("Answer: "), "")
        mock_get_input.assert_called_with("Answer: ")

    @patch("cs50.cs50._get_input", return_value="test")
    def test_get_string_nonempty_input(self, mock_get_input):
        """Returns the provided non-empty input"""
        self.assertEqual(get_string("Answer: "), "test")
        mock_get_input.assert_called_with("Answer: ")

    @patch("cs50.cs50._get_input", side_effect=EOFError)
    def test_get_string_eof(self, mock_get_input):
        """Returns None on EOF"""
        self.assertIs(get_string("Answer: "), None)
        mock_get_input.assert_called_with("Answer: ")

    def test_get_string_invalid_prompt(self):
        """Raises TypeError when prompt is not str"""
        with self.assertRaises(TypeError):
            get_string(1)

    @patch("cs50.cs50.get_string", return_value=None)
    def test_get_int_eof(self, mock_get_string):
        """Returns None on EOF"""
        self.assertIs(_get_int("Answer: "), None)
        mock_get_string.assert_called_with("Answer: ")

    def test_get_int_valid_input(self):
        """Returns the provided integer input"""

        def assert_equal(return_value, expected_value):
            with patch("cs50.cs50.get_string", return_value=return_value) as mock_get_string:
                self.assertEqual(_get_int("Answer: "), expected_value)
                mock_get_string.assert_called_with("Answer: ")

        values = [
            ("0", 0),
            ("50", 50),
            ("+50", 50),
            ("+42", 42),
            ("-42", -42),
            ("42", 42),
        ]

        for return_value, expected_value in values:
            assert_equal(return_value, expected_value)

    def test_get_int_invalid_input(self):
        """Raises ValueError when input is invalid base-10 int"""

        def assert_raises_valueerror(return_value):
            with patch("cs50.cs50.get_string", return_value=return_value) as mock_get_string:
                with self.assertRaises(ValueError):
                    _get_int("Answer: ")

                mock_get_string.assert_called_with("Answer: ")

        return_values = [
            "++50",
            "--50",
            "50+",
            "50-",
            " 50",
            " +50",
            " -50",
            "50 ",
            "ab50",
            "50ab",
            "ab50ab",
        ]

        for return_value in return_values:
            assert_raises_valueerror(return_value)

    @patch("cs50.cs50.get_string", return_value=None)
    def test_get_float_eof(self, mock_get_string):
        """Returns None on EOF"""
        self.assertIs(_get_float("Answer: "), None)
        mock_get_string.assert_called_with("Answer: ")

    def test_get_float_valid_input(self):
        """Returns the provided integer input"""
        def assert_equal(return_value, expected_value):
            with patch("cs50.cs50.get_string", return_value=return_value) as mock_get_string:
                f = _get_float("Answer: ")
                self.assertAlmostEqual(f, expected_value)
                mock_get_string.assert_called_with("Answer: ")

        values = [
            (".0", 0.0),
            ("0.", 0.0),
            (".42", 0.42),
            ("42.", 42.0),
            ("50", 50.0),
            ("+50", 50.0),
            ("-50", -50.0),
            ("+3.14", 3.14),
            ("-3.14", -3.14),
        ]

        for return_value, expected_value in values:
            assert_equal(return_value, expected_value)

    def test_get_float_invalid_input(self):
        """Raises ValueError when input is invalid float"""

        def assert_raises_valueerror(return_value):
            with patch("cs50.cs50.get_string", return_value=return_value) as mock_get_string:
                with self.assertRaises(ValueError):
                    _get_float("Answer: ")

                mock_get_string.assert_called_with("Answer: ")

        return_values = [
            ".",
            "..5",
            "a.5",
            ".5a"
            "0.5a",
            "a0.42",
            " .42",
            "3.14 ",
            "++3.14",
            "3.14+",
            "--3.14",
            "3.14--",
        ]

        for return_value in return_values:
            assert_raises_valueerror(return_value)
