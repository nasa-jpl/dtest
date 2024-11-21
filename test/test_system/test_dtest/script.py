from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import unittest
import subprocess


class SystemTests(unittest.TestCase):
    def setUp(self):
        """Automatically called before each test* method."""
        import tempfile

        self.__temporary_file_path = tempfile.mkdtemp()

    def tearDown(self):
        """Automatically called after each test* method."""
        import shutil

        shutil.rmtree(path=self.__temporary_file_path, ignore_errors=True)

    def testSingleProcessTest(self):
        self._runProcess(["dtest"])

    def testMultiProcessTest(self):
        self.assertEqual(
            "SUMMARY: Ran 4 tests, 2 succeeded, 2 failed",
            self._runProcess(["dtest", "--jobs=10", "--short-summary"]),
        )

    def testMultiProcessTest(self):
        self.assertEqual(
            "SUMMARY: Ran 4 tests, 2 succeeded, 2 failed",
            self._runProcess(["dtest", "--jobs=10", "--short-summary"]),
        )

    def testMultiProcessTestMediumSummary(self):
        self._runProcess(["dtest", "--jobs=10"])
        """
        self.assertEqual('SUMMARY: Ran 4 tests, 2 succeeded, 2 failed',
                         self._runProcess(['dtest', '--jobs=10']))
        """

    def testIgnoreSingle(self):
        self.assertEqual(
            "SUMMARY: Ran 3 tests, 1 succeeded, 2 failed",
            self._runProcess(["dtest", "--ignore=*one"]),
        )

    def testIgnoreNoMatch(self):
        self.assertEqual(
            "SUMMARY: Ran 4 tests, 2 succeeded, 2 failed",
            self._runProcess(["dtest", "--ignore=*no_match_here*"]),
        )

    def _runProcess(self, command_list):
        test_root = _makeFakeTests(self.__temporary_file_path)

        process = subprocess.Popen(
            command_list + ["-d", test_root],
            stdout=subprocess.PIPE,
            cwd=self.__temporary_file_path,
        )
        output_lines = process.communicate()[0].decode("utf-8").splitlines()

        import os

        data_filename = os.path.join(test_root, "regtest.data")
        self.assertTrue(os.path.exists(data_filename))
        # Make sure it is valid Python.
        subprocess.check_call(["python", data_filename])

        report_filename = os.path.join(test_root, "report")
        self.assertTrue(os.path.exists(report_filename))
        with open(report_filename) as report:
            self.assertIn("SUMMARY:", report.read())

        summary_lines = [l for l in output_lines if l.startswith("SUMMARY: ")]
        self.assertEqual(1, len(summary_lines))
        return summary_lines[0]


def _makeFakeTests(path):
    """Make a fake test.

    -+= path
     \-+= test
       |--= test_one (succeed)
       |-+= test_two
       | |--= test_alpha (succeed)
       | \--= test_beta (empty)
       \--= test_three (fail)

    """
    import os

    test_root = os.path.join(path, "test")
    os.mkdir(test_root)

    with open(os.path.join(test_root, "DTESTDEFS"), "w") as config_file:
        config_file.write(
            """[RUN]
    test = bash script.bash >& output
"""
        )

    # test_one should succeed
    one = os.path.join(test_root, "test_one")
    os.mkdir(one)
    _writeBashScript(one, contents="echo > /dev/null")

    os.mkdir(os.path.join(test_root, "test_two"))

    # test_two should succeed
    alpha = os.path.join(test_root, "test_two", "test_alpha")
    os.mkdir(alpha)
    _writeBashScript(alpha, contents="echo > /dev/null")

    # Leave this empty for expected failure
    os.mkdir(os.path.join(test_root, "test_two", "test_beta"))

    # test_three should fail
    three = os.path.join(test_root, "test_three")
    os.mkdir(three)
    _writeBashScript(three, contents="non_existent_command")

    return test_root


def _writeBashScript(path, contents):
    """Write a bash script."""
    import os

    with open(os.path.join(path, "script.bash"), "w") as output_file:
        output_file.write("#!/bin/bash\n")
        output_file.write(contents)

    with open(os.path.join(path, "output.orig"), "w") as output_file:
        output_file.write("")


if __name__ == "__main__":
    unittest.main()
