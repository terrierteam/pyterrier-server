import unittest


class TestPyterrierServe(unittest.TestCase):
    def test_import(self):
        try:
            import pyterrier_serve
        except ImportError as e:
            self.fail(f"Import failed: {e}")
