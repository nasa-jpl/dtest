import os, sys
import stat
import time, datetime
import pandas as pd
import h5py
import numpy as np
import collections
import datetime


class TestInfo:
    def __init__(
        self,
        name,
        passed,
        module,
        module_release,
        num_runs_ok,
        num_runs,
        num_cmps_ok,
        num_cmps,
        start_time,
        elapsed_time,
        timed_out,
    ):
        self.name = name
        self.passed = passed
        self.module = module
        self.module_release = module_release
        self.num_runs_ok = num_runs_ok
        self.num_runs = num_runs
        self.num_cmps_ok = num_cmps_ok
        self.num_cmps = num_cmps
        self.start_time = start_time
        self.elapsed_time = elapsed_time
        self.timed_out = timed_out

    def __str__(self):
        title_str = f"TEST:\t{self.name}\nMODULE:\t{self.module} (release {self.module_release})"
        passed_str = f"\tPassed:\t\t{self.passed}"
        timed_out_str = f"\tTimed out:\t{self.timed_out}"
        start_time_str = f"\tStart time:\t{self.start_time}"
        elapsed_time_str = f"\tElapsed time:\t{self.elapsed_time} seconds"
        runs_str = f"\tRuns:\t\t{self.num_runs_ok}/{self.num_runs}"
        cmps_str = f"\tComparisons:\t{self.num_cmps_ok}/{self.num_cmps}"

        return (
            f"{title_str}\n{passed_str}\n{timed_out_str}\n{start_time_str}\n{elapsed_time_str}\n{runs_str}\n{cmps_str}"
        )


# returns (test_found, passed)
def checkPassed(f, file_key, module_name, test_name):
    # make sure the file name is a valid key
    if file_key not in list(f.keys()):
        return (False, False)

    # get the group corresponding to the latest test
    file_group = f[file_key]

    # check that the module exists
    if module_name not in list(file_group.keys()):
        return (False, False)

    # get the dataset of tests for the module
    module_dataset = file_group[module_name]
    # get the names of the tests - must decode the byte strings
    test_names = np.array([x.decode("ascii") for x in module_dataset["name"]])

    # check that the test exists
    if test_name not in test_names:
        return (False, False)

    # check that the test passed
    # get the row corresponding to the test -- squeeze to remove extra dimension
    test_row = module_dataset[test_names == test_name].squeeze()
    # check if passed
    passed = test_row["passed"]

    return (True, passed)


# assumes that the file_key, module, and test exist
def getTestInfo(f, file_key, module_name, test_name):
    module_dataset = f[f"{file_key}/{module_name}"]

    # get the names of the tests - must decode the byte strings
    test_names = np.array([x.decode("ascii") for x in module_dataset["name"]])

    test_row = module_dataset[test_names == test_name].squeeze()

    test_info = TestInfo(
        name=test_name,
        passed=test_row["passed"],
        module=module_name,
        module_release=module_dataset.attrs["release"],
        num_runs_ok=test_row["num_runs_ok"],
        num_runs=test_row["num_runs"],
        num_cmps_ok=test_row["num_comparisons_ok"],
        num_cmps=test_row["num_comparisons"],
        start_time=test_row["start_time"].astype("U30"),
        elapsed_time=test_row["elapsed_time"].astype("U30"),
        timed_out=test_row["timed_out"],
    )

    return test_info


# assumes file_keys are valid
def printModuleDiff(f, old_file_key, new_file_key):
    old_file_group = f[old_file_key]
    new_file_group = f[new_file_key]

    # get a list of all modules and their releases
    module_names = list(new_file_group.keys())

    for module_name in module_names:
        old_release = old_file_group[module_name].attrs["release"]
        new_release = new_file_group[module_name].attrs["release"]
        if old_release != new_release:
            print(f"MODULE {module_name}:\t{old_release} -> {new_release}")
        # else:
        #     print(f"No changes in module {module_name}")


def findLastPassed(f, module_name, test_name):
    sorted_file_keys = sorted(list(f.keys()), reverse=True)

    # first check the latest regtests and
    #   1) make sure the module/regtest exist
    #   2) check if the regtest actually failed
    (test_found, passed) = checkPassed(f, sorted_file_keys[0], module_name, test_name)

    if not test_found:
        print("Module or test not found!")
        return

    if passed:
        print("Test is passing!")
        return

    # if we get to here, we know the test exists, and is failing
    # so get the test/module info at this time
    latest_test_info = getTestInfo(f, sorted_file_keys[0], module_name, test_name)
    print("\n\nFailing test:")
    print(latest_test_info)

    # iterate through the past regtests and try and find where this test has succeeded
    for key_ind, file_key in enumerate(sorted_file_keys):
        (test_found, passed) = checkPassed(f, file_key, module_name, test_name)

        # if test does not exist, print the module release when it was introduced
        # i.e. test never passed since it was introduced
        if not test_found:
            print(f"Test not found in {file_key}")
            return

        # if the test passed, we're done - we found the last time the test passed
        if passed:
            # print the test info from when it last passed
            test_info = getTestInfo(f, file_key, module_name, test_name)
            print("\n\nSuccessful test:")
            print(f"{test_info}")

            # print what modules have changed in between this test passing and first failing
            printModuleDiff(f, sorted_file_keys[key_ind - 1], file_key)

            return

    # if we get to here, we have searched through every regtest in the HDF5 file and not found the test passing
    print("Test has never passed!")


if __name__ == "__main__":
    with h5py.File("hierarchical_test.h5") as f:
        # find a test
        findLastPassed(f, "SCM", "test_scmPython")
