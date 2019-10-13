import sys

sys.path.insert(0, "../src")

import cs50

def test_get_int():
    """
    Tests the get_int() function
    """
    i = cs50.get_int("Integer: ")
    assert type(i) == type(0), "get_int() did not return an integer"

def test_get_float():
    """
    Tests the get_float() function
    """
    i = cs50.get_float("Float: ")
    assert type(i) == type(0.0), "get_float() did not return a float"

def test_get_string():
    """
    Tests the get_string() function
    """
    i = cs50.get_string("String: ")
    assert type(i) == type(""), "get_string() did not return a string"

if __name__ == "__main__":
    test_get_int()
    test_get_float()
    test_get_string()
    print("All tests passed!")