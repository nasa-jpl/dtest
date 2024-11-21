from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import os
import unittest
from Dtest import Test
from Dtest import configobj


class MainTests(unittest.TestCase):
    def setUp(self):
        """Automatically called before each test* method."""
        import tempfile

        self.__temporary_file_path = tempfile.mkdtemp()

        Test.log = lambda *_: None
        Test.logTee = lambda *_: None

    def tearDown(self):
        """Automatically called after each test* method."""
        import shutil

        shutil.rmtree(path=self.__temporary_file_path, ignore_errors=True)

    def testRunUnitTest(self):
        config = configobj.ConfigObj()
        config["RUN"] = {"test1": "ls"}
        config["TIMEOUT"] = -1
        print(
            filter_results(
                Test.runUnitTest(
                    new_config=config,
                    full_dir=self.__temporary_file_path,
                    root_dir=self.__temporary_file_path,
                    truth_suffix="",
                    test_command_modifier=lambda cmd, _, __: cmd,
                    log_num=0,
                )
            )
        )
        self.assertEqual(
            (
                1,
                0,
                {
                    "run": (1, 1),
                    "timed_out": 0,
                    "cmp": (0, 0),
                    "sub_tests": {"ls": {"completion_status": True, "return_code": 0}},
                    "sub_cmps": {},
                },
            ),
            filter_results(
                Test.runUnitTest(
                    new_config=config,
                    full_dir=self.__temporary_file_path,
                    root_dir=self.__temporary_file_path,
                    truth_suffix="",
                    test_command_modifier=lambda cmd, _, __: cmd,
                    log_num=0,
                )
            ),
        )

    def testRunUnitTestFailure(self):
        config = configobj.ConfigObj()
        config["RUN"] = {"test1": "junkjunkjunkcommand"}
        config["TIMEOUT"] = -1
        print(
            filter_results(
                Test.runUnitTest(
                    new_config=config,
                    full_dir=self.__temporary_file_path,
                    root_dir=self.__temporary_file_path,
                    truth_suffix="",
                    test_command_modifier=lambda cmd, _, __: cmd,
                    log_num=0,
                )
            )
        )
        self.assertEqual(
            (
                0,
                1,
                {
                    "run": (0, 1),
                    "timed_out": 0,
                    "cmp": (0, 0),
                    "sub_tests": {
                        "junkjunkjunkcommand": {
                            "completion_status": False,
                            "return_code": 127,
                        }
                    },
                    "sub_cmps": {},
                },
            ),
            filter_results(
                Test.runUnitTest(
                    new_config=config,
                    full_dir=self.__temporary_file_path,
                    root_dir=self.__temporary_file_path,
                    truth_suffix="",
                    test_command_modifier=lambda cmd, _, __: cmd,
                    log_num=0,
                )
            ),
        )

    def testRunUnitTestTimeout(self):
        config = configobj.ConfigObj()
        config["RUN"] = {"test1": "python"}
        config["TIMEOUT"] = 0
        print(
            filter_results(
                Test.runUnitTest(
                    new_config=config,
                    full_dir=self.__temporary_file_path,
                    root_dir=self.__temporary_file_path,
                    truth_suffix="",
                    test_command_modifier=lambda cmd, _, __: cmd,
                    log_num=0,
                )
            )
        )
        self.assertEqual(
            (
                0,
                1,
                {
                    "run": (0, 1),
                    "timed_out": 1,
                    "cmp": (0, 0),
                    "sub_cmps": {},
                    "sub_tests": {
                        "python": {
                            "completion_status": False,
                            "return_code": "TimeoutExpired(0)",
                        }
                    },
                },
            ),
            filter_results(
                Test.runUnitTest(
                    new_config=config,
                    full_dir=self.__temporary_file_path,
                    root_dir=self.__temporary_file_path,
                    truth_suffix="",
                    test_command_modifier=lambda cmd, _, __: cmd,
                    log_num=0,
                )
            ),
        )

    def testRunUnitTestWithDeletion(self):
        config = configobj.ConfigObj()
        config["RUN"] = {"test1": "ls"}
        config["TIMEOUT"] = -1
        config["DELETE"] = ("junk",)

        junk_filename = os.path.join(self.__temporary_file_path, "junk")
        with open(junk_filename, "w") as f:
            f.write("")

        self.assertTrue(os.path.exists(junk_filename))
        print(
            filter_results(
                Test.runUnitTest(
                    new_config=config,
                    full_dir=self.__temporary_file_path,
                    root_dir=self.__temporary_file_path,
                    truth_suffix="",
                    test_command_modifier=lambda cmd, _, __: cmd,
                    log_num=0,
                )
            )
        )
        self.assertEqual(
            (
                1,
                0,
                {
                    "run": (1, 1),
                    "timed_out": 0,
                    "cmp": (0, 0),
                    "sub_cmps": {},
                    "sub_tests": {"ls": {"completion_status": True, "return_code": 0}},
                },
            ),
            filter_results(
                Test.runUnitTest(
                    new_config=config,
                    full_dir=self.__temporary_file_path,
                    root_dir=self.__temporary_file_path,
                    truth_suffix="",
                    test_command_modifier=lambda cmd, _, __: cmd,
                    log_num=0,
                )
            ),
        )

        self.assertFalse(os.path.exists(junk_filename))

    def testRunUnitTestShouldNotDeleteOnFailure(self):
        config = configobj.ConfigObj()
        config["RUN"] = {"test1": "junkjunkjunkcommand"}
        config["TIMEOUT"] = -1
        config["DELETE"] = ("junk",)

        junk_filename = os.path.join(self.__temporary_file_path, "junk")
        with open(junk_filename, "w") as f:
            f.write("")

        self.assertTrue(os.path.exists(junk_filename))
        print(
            filter_results(
                Test.runUnitTest(
                    new_config=config,
                    full_dir=self.__temporary_file_path,
                    root_dir=self.__temporary_file_path,
                    truth_suffix="",
                    test_command_modifier=lambda cmd, _, __: cmd,
                    log_num=0,
                )
            )
        )
        self.assertEqual(
            (
                0,
                1,
                {
                    "run": (0, 1),
                    "timed_out": 0,
                    "cmp": (0, 0),
                    "sub_tests": {
                        "junkjunkjunkcommand": {
                            "completion_status": False,
                            "return_code": 127,
                        }
                    },
                    "sub_cmps": {},
                },
            ),
            filter_results(
                Test.runUnitTest(
                    new_config=config,
                    full_dir=self.__temporary_file_path,
                    root_dir=self.__temporary_file_path,
                    truth_suffix="",
                    test_command_modifier=lambda cmd, _, __: cmd,
                    log_num=0,
                )
            ),
        )

        self.assertTrue(os.path.exists(junk_filename))

    def testRunUnitTestWithComparison(self):
        config = configobj.ConfigObj()
        config["RUN"] = {"test1": "ls"}
        config["TIMEOUT"] = -1
        config["CMP"] = ("echo",)

        with open(os.path.join(self.__temporary_file_path, "me.orig"), "w"):
            pass
        with open(os.path.join(self.__temporary_file_path, "me"), "w"):
            pass
        print(
            filter_results(
                Test.runUnitTest(
                    new_config=config,
                    full_dir=self.__temporary_file_path,
                    root_dir=self.__temporary_file_path,
                    truth_suffix="",
                    test_command_modifier=lambda cmd, _, __: cmd,
                    log_num=0,
                )
            )
        )
        self.assertEqual(
            (
                1,
                0,
                {
                    "run": (1, 1),
                    "timed_out": 0,
                    "cmp": (1, 1),
                    "sub_cmps": {
                        "echo me.orig me": {
                            "completion_status": True,
                            "return_code": 0,
                        }
                    },
                    "sub_tests": {"ls": {"completion_status": True, "return_code": 0}},
                },
            ),
            filter_results(
                Test.runUnitTest(
                    new_config=config,
                    full_dir=self.__temporary_file_path,
                    root_dir=self.__temporary_file_path,
                    truth_suffix="",
                    test_command_modifier=lambda cmd, _, __: cmd,
                    log_num=0,
                )
            ),
        )

    def testRunUnitTestWithComparisonForSpecificSuffix(self):
        config = configobj.ConfigObj()
        config["RUN"] = {"test1": "ls"}
        config["TIMEOUT"] = -1
        config["COMPARE"] = {r".*\.foobar$": ("echo",)}

        with open(os.path.join(self.__temporary_file_path, "me.foobar.orig"), "w"):
            pass
        with open(os.path.join(self.__temporary_file_path, "me.foobar"), "w"):
            pass
        print(
            filter_results(
                Test.runUnitTest(
                    new_config=config,
                    full_dir=self.__temporary_file_path,
                    root_dir=self.__temporary_file_path,
                    truth_suffix="",
                    test_command_modifier=lambda cmd, _, __: cmd,
                    log_num=0,
                )
            )
        )
        self.assertEqual(
            (
                1,
                0,
                {
                    "run": (1, 1),
                    "timed_out": 0,
                    "cmp": (1, 1),
                    "sub_cmps": {
                        "echo me.foobar.orig me.foobar": {
                            "completion_status": True,
                            "return_code": 0,
                        }
                    },
                    "sub_tests": {"ls": {"completion_status": True, "return_code": 0}},
                },
            ),
            filter_results(
                Test.runUnitTest(
                    new_config=config,
                    full_dir=self.__temporary_file_path,
                    root_dir=self.__temporary_file_path,
                    truth_suffix="",
                    test_command_modifier=lambda cmd, _, __: cmd,
                    log_num=0,
                )
            ),
        )

    def testRunUnitTestWithComparisonAndAlternateTruthSuffix(self):
        config = configobj.ConfigObj()
        config["RUN"] = {"test1": "ls"}
        config["TIMEOUT"] = -1
        config["COMPARE"] = {r".*\.foobar$": ("echo",)}
        config["TRUTHSUFFIX"] = "hello"

        with open(os.path.join(self.__temporary_file_path, "me.foobar.hello"), "w"):
            pass
        with open(os.path.join(self.__temporary_file_path, "me.foobar"), "w"):
            pass
        print(
            filter_results(
                Test.runUnitTest(
                    new_config=config,
                    full_dir=self.__temporary_file_path,
                    root_dir=self.__temporary_file_path,
                    truth_suffix="",
                    test_command_modifier=lambda cmd, _, __: cmd,
                    log_num=0,
                )
            )
        )
        self.assertEqual(
            (
                1,
                0,
                {
                    "run": (1, 1),
                    "timed_out": 0,
                    "cmp": (1, 1),
                    "sub_cmps": {
                        "echo me.foobar.hello me.foobar": {
                            "completion_status": True,
                            "return_code": 0,
                        }
                    },
                    "sub_tests": {"ls": {"completion_status": True, "return_code": 0}},
                },
            ),
            filter_results(
                Test.runUnitTest(
                    new_config=config,
                    full_dir=self.__temporary_file_path,
                    root_dir=self.__temporary_file_path,
                    truth_suffix="",
                    test_command_modifier=lambda cmd, _, __: cmd,
                    log_num=0,
                )
            ),
        )

    def testRunUnitTestWithComparisonAndAlternateTruthSuffixMulti(self):
        config = configobj.ConfigObj()
        config["RUN"] = {"test1": "ls"}
        config["TIMEOUT"] = -1
        config["COMPARE"] = {r".*\.foobar$": ("diff",)}
        config["TRUTHSUFFIX"] = ("truth", "truth2")

        # Create the test files
        with open(os.path.join(self.__temporary_file_path, "me.foobar.truth"), "w") as f:
            print("Hello!", file=f)
        with open(os.path.join(self.__temporary_file_path, "me.foobar.truth2"), "w") as f:
            print("Hello", file=f)
        with open(os.path.join(self.__temporary_file_path, "me.foobar"), "w") as f:
            print("Hello", file=f)
        print(
            filter_results(
                Test.runUnitTest(
                    new_config=config,
                    full_dir=self.__temporary_file_path,
                    root_dir=self.__temporary_file_path,
                    truth_suffix="",
                    test_command_modifier=lambda cmd, _, __: cmd,
                    log_num=0,
                )
            )
        )
        self.assertEqual(
            (
                1,
                0,
                {
                    "run": (1, 1),
                    "timed_out": 0,
                    "cmp": (1, 1),
                    "sub_cmps": {
                        "diff me.foobar.truth me.foobar": {
                            "completion_status": False,
                            "return_code": 1,
                        },
                        "diff me.foobar.truth2 me.foobar": {
                            "completion_status": True,
                            "return_code": 0,
                        },
                    },
                    "sub_tests": {"ls": {"completion_status": True, "return_code": 0}},
                },
            ),
            filter_results(
                Test.runUnitTest(
                    new_config=config,
                    full_dir=self.__temporary_file_path,
                    root_dir=self.__temporary_file_path,
                    truth_suffix="",
                    test_command_modifier=lambda cmd, _, __: cmd,
                    log_num=0,
                )
            ),
        )

    def testRunUnitTestWithEnvironmentVariable(self):
        config = configobj.ConfigObj()
        config["ENV"] = {"MY_TEST_ENV": "hello world"}
        config["RUN"] = {
            "test1": '[ "hello world" == "$MY_TEST_ENV" ]',
            "test2": '[ "hello world" != "$MY_NON_EXISTENT_ENV" ]',
        }
        config["TIMEOUT"] = -1
        print(
            filter_results(
                Test.runUnitTest(
                    new_config=config,
                    full_dir=self.__temporary_file_path,
                    root_dir=self.__temporary_file_path,
                    truth_suffix="",
                    test_command_modifier=lambda cmd, _, __: cmd,
                    log_num=0,
                )
            )
        )
        self.assertEqual(
            (
                1,
                0,
                {
                    "run": (2, 2),
                    "timed_out": 0,
                    "cmp": (0, 0),
                    "sub_cmps": {},
                    "sub_tests": {
                        '[ "hello world" != "$MY_NON_EXISTENT_ENV" ]': {
                            "completion_status": True,
                            "return_code": 0,
                        },
                        '[ "hello world" == "$MY_TEST_ENV" ]': {
                            "completion_status": True,
                            "return_code": 0,
                        },
                    },
                },
            ),
            filter_results(
                Test.runUnitTest(
                    new_config=config,
                    full_dir=self.__temporary_file_path,
                    root_dir=self.__temporary_file_path,
                    truth_suffix="",
                    test_command_modifier=lambda cmd, _, __: cmd,
                    log_num=0,
                )
            ),
        )


class UtilityTests(unittest.TestCase):
    def testLock(self):
        import tempfile

        temporary_directory = tempfile.mkdtemp(dir=".")
        lock_filename = os.path.join(temporary_directory, "my_lock")

        with Test.lock(lock_filename):
            with self.assertRaises(Test.LockException) as exception:
                with Test.lock(lock_filename):
                    pass
            self.assertIn("my_lock", str(exception.exception))

        got_lock = False
        with Test.lock(lock_filename):
            got_lock = True
        self.assertTrue(got_lock)

        os.rmdir(temporary_directory)


def filter_results(result):
    """Remove non-deterministic keys."""
    a = result[0]
    b = result[1]
    dictionary = {k: result[2][k] for k in result[2] if k != "elapsed_time"}
    return (a, b, dictionary)


if __name__ == "__main__":
    unittest.main()
