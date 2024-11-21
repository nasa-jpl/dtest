from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import unittest


class Tests(unittest.TestCase):
    def test_bad(self):
        self.assertEqual(1, 2)
