from .cs50 import *

class CustomImporter(object):
    """
    Import cs50.SQL lazily.

    http://dangerontheranger.blogspot.com/2012/07/how-to-use-sysmetapath-with-python.html
    """
    def find_module(self, fullname, path=None):
        if fullname == "cs50.SQL":
            return self
        return None
    def load_module(self, fullname):
        print("1")
        if fullname != "cs50.SQL":
            raise ImportError(fullname)
        print("2")
        from .sql import SQL
        print("3")
        return SQL
sys.meta_path.append(CustomImporter())
