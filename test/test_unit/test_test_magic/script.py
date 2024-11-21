from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import unittest

from Dtest import TestMagic


class TestMagicTestCase(unittest.TestCase):
    def setUp(self):
        """Automatically called before each test* method."""

    def tearDown(self):
        """Automatically called after each test* method."""

    def testMagicFileWorksWithPNG(self):
        self.assertIn("image data", TestMagic.magicString("image.png"))

    def testMagicFileWorksWithJPEG(self):
        self.assertIn("image data", TestMagic.magicString("image.jpg"))

    def testMagicFileWorksWithExecutableELF(self):
        self.assertIn("executable", TestMagic.magicString("executable_elf"))
        self.assertIn("ELF", TestMagic.magicString("executable_elf"))


if __name__ == "__main__":
    unittest.main()
