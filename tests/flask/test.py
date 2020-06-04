from application import app
import logging
import requests
import sys
import threading
import time
import unittest


def request(route):
    r = requests.get("http://localhost:5000/{}".format(route))
    return r.text == "True"

class FlaskTests(unittest.TestCase):

    def test__create(self):
        self.assertTrue(request("create"))
 
    def test_autocommit(self):
        self.assertTrue(request("autocommit"))

    def test_delete(self):
        self.assertTrue(request("delete"))

    def test_insert(self):
        self.assertTrue(request("insert"))

    def test_multiple_connections(self):
        self.assertTrue(request("multiple_connections"))

    def test_select(self):
        self.assertTrue(request("select"))

    def test_single_teardown(self):
        self.assertTrue(request("single_teardown"))

    def test_zdrop(self):
        self.assertTrue(request("drop"))


if __name__ == "__main__":
    t = threading.Thread(target=app.run, daemon=True)
    t.start()

    suite = unittest.TestSuite([
        unittest.TestLoader().loadTestsFromTestCase(FlaskTests)
    ])

    sys.exit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
