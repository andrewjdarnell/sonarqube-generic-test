import unittest

class TestAdvanced(unittest.TestCase):
    def test_power(self):
        self.assertEqual(pow(2, 3), 8)

    def test_modulo(self):
        self.assertEqual(10 % 3, 1)
