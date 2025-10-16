import unittest


class TestPyterrierServer(unittest.TestCase):
    def test_import(self):
        try:
            import pyterrier_server
        except ImportError as e:
            self.fail(f"Import failed: {e}")
