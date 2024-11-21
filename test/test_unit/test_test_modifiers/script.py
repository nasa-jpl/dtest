from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import unittest

from Dtest import TestModifiers


class TestModifiersTestCase(unittest.TestCase):
    def setUp(self):
        """Automatically called before each test* method."""

    def tearDown(self):
        """Automatically called after each test* method."""

    def testIsPythonFile(self):
        self.assertTrue(TestModifiers.isPythonFile("script.py"))
        self.assertTrue(TestModifiers.isPythonFile("executable_script.py"))
        self.assertTrue(TestModifiers.isPythonFile("foo"))

        self.assertFalse(TestModifiers.isPythonFile("non_existent_file.py"))
        self.assertFalse(TestModifiers.isPythonFile("NonExistentFilePy"))

    def testPythonCoverageModifierWithLocalExecutable(self):
        self.assertEqual(
            TestModifiers.pythonCoverageModifier("./executable_script.py", ".", lambda x: None),
            "coverage run --parallel-mode --branch ./executable_script.py",
        )

    def testPythonCoverageModifierWithSandboxExecutable(self):
        self.assertEqual(
            TestModifiers.pythonCoverageModifier("./foo", ".", lambda x: None),
            "coverage run --parallel-mode --branch ./foo",
        )

    def testMemcheckModifier(self):
        self.assertEqual(
            "valgrind --tool=memcheck --error-exitcode=77 --leak-check=full "
            "--quiet --log-file=_executable_elf.memcheck.log ./executable_elf",
            TestModifiers.memcheckModifier("./executable_elf", ".", lambda x: None),
        )

    def testHelgrindModifier(self):
        self.assertEqual(
            "valgrind --tool=helgrind --error-exitcode=77 --quiet "
            "--log-file=_executable_elf.helgrind.log ./executable_elf",
            TestModifiers.helgrindModifier("./executable_elf", ".", lambda x: None),
        )

    def testCatchsegvModifier(self):
        self.assertEqual(
            "catchsegv python executable_script.py",
            TestModifiers.catchsegvModifier("catchsegv python executable_script.py", ".", lambda x: None),
        )

        self.assertEqual(
            "! python executable_script.py",
            TestModifiers.catchsegvModifier("! python executable_script.py", ".", lambda x: None),
        )


if __name__ == "__main__":
    unittest.main()
