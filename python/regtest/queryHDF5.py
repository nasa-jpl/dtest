import os, sys
import stat
import time, datetime
import pandas as pd
import warnings
import traceback

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=UserWarning)
    import h5py
import numpy as np
import collections
import datetime


# a class to store information about an individual test
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
        file_key,
        last_passed_file_key,
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
        self.file_key = file_key
        self.last_passed_file_key = last_passed_file_key

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


# a class to store information about a module
class ModuleInfo:
    def __init__(self, name, release, num_tests_ok, num_tests, tests, start_time, elapsed_time):
        self.name = name
        self.release = release
        self.num_tests_ok = num_tests_ok
        self.num_tests = num_tests
        self.tests = tests
        self.start_time = start_time
        self.elapsed_time = elapsed_time

    def __str__(self):
        title_str = f"MODULE:\t{self.name} (release {self.release})"
        tests_str = f"\tTests:\t\t{self.num_tests_ok}/{self.num_tests}"
        failed_tests_str = f"\tFailed tests:\t{', '.join([t.name for t in self.tests if not t.passed])}"
        start_time_str = f"\tStart time:\t{self.start_time}"
        elapsed_time_str = f"\tElapsed time:\t{self.elapsed_time}"

        return f"{title_str}\n{start_time_str}\n{elapsed_time_str}\n{tests_str}\n{failed_tests_str}"


# a class to store information about a run
class RunInfo:
    def __init__(self, filename, num_tests_ok, num_tests, start_time):
        self.filename = filename
        self.num_tests_ok = num_tests_ok
        self.num_tests = num_tests
        self.start_time = start_time

    def __str__(self):
        title_str = f"FILENAME:\t{self.filename}"
        tests_str = f"\tTests:\t\t{self.num_tests_ok}/{self.num_tests} ({100*self.num_tests_ok/self.num_tests:.1f}%)"
        start_time_str = f"\tStart time:\t{self.start_time}"

        return f"{title_str}\n{tests_str}\n{start_time_str}"


##########################################
# API Endpoints
##########################################


# given a HDF5 filename, returns stats for the last num_past_runs runs, starting at the latest run
#   hdf5_filename - the filename to read HDF5 data from
#   num_past_runs - the number of past runs to return info for
#   date - the datetime object that corresponds to the file entry. Will find the closest entry to the given date, if not None.
#   sandboxes - an array of sandboxes to consider when finding files. Will only look in files from the array of sandboxes, if not None.
def runStats(hdf5_filename, sandbox, num_past_runs=1, date=None):
    with h5py.File(hdf5_filename, libver="latest") as f:
        run_infos = _runStats(f, sandbox, num_past_runs, date)

    return run_infos


# given a HDF5 filename and module name, returns stats for the last num_past_runs runs, starting at the latest run (if date is None)
#   hdf5_filename - the filename to read HDF5 data from
#   module_name - the name of the module to get info for
#   num_past_runs - the number of past runs to return info for
#   get_test_infos - whether or not to get all the TestInfos for each test. More informative, but much slower and sometimes not necessary.
#   date - the datetime object that corresponds to the file entry. Will find the closest entry to the given date, if not None.
#   sandboxes - an array of sandboxes to consider when finding files. Will only look in files from the array of sandboxes, if not None.
def moduleStats(hdf5_filename, sandbox, module_name, num_past_runs=1, get_test_infos=True, date=None):
    with h5py.File(hdf5_filename, libver="latest") as f:
        module_infos = _moduleStats(f, sandbox, module_name, num_past_runs, get_test_infos, date)

    return module_infos


# given a HDF5 filename and an array of module names, returns stats for the last num_past_runs runs for each module in module_names
# when getting info for multiple modules at once, this is faster than multiple calls to moduleStats
#   hdf5_filename - the filename to read HDF5 data from
#   module_names - array of module names to get info for
#   num_past_runs - the number of past runs to return info for
#   get_test_infos - whether or not to get all the TestInfos for each test. More informative, but much slower and sometimes not necessary.
#   date - the datetime object that corresponds to the file entry. Will find the closest entry to the given date, if not None.
#   sandboxes - an array of sandboxes to consider when finding files. Will only look in files from the array of sandboxes, if not None.
def multipleModuleStats(
    hdf5_filename,
    sandbox,
    module_names,
    num_past_runs=1,
    get_test_infos=True,
    date=None,
):
    with h5py.File(hdf5_filename, libver="latest") as f:
        multiple_module_infos = []
        for module_name in module_names:
            module_infos = _moduleStats(f, sandbox, module_name, num_past_runs, get_test_infos, date)
            multiple_module_infos.append(module_infos)

    return multiple_module_infos


# given a HDF5 filename, module name, and test name, returns stats for the last num_past_runs runs, starting at the latest run
#   hdf5_filename - the filename to read HDF5 data from
#   module_name - the name of the module the test is located in
#   test_name - the name of the test to return info for
#   num_past_runs - the number of past runs to return info for
#   date - the datetime object that corresponds to the file entry. Will find the closest entry to the given date, if not None.
#   sandboxes - an array of sandboxes to consider when finding files. Will only look in files from the array of sandboxes, if not None.
def testStats(hdf5_filename, sandbox, module_name, test_name, num_past_runs, date=None):
    with h5py.File(hdf5_filename, libver="latest") as f:
        test_infos = _testStats(f, sandbox, module_name, test_name, num_past_runs, date)

    return test_infos


# given a HDF5 filename, module name, and test name, find the last time this test passed
#   hdf5_filename - the filename to read HDF5 data from
#   module_name - the name of the module the test is located in
#   test_name - the name of the test to return info for
def findLastPassed(hdf5_filename, module_name, test_name, date=None):
    with h5py.File(hdf5_filename, libver="latest") as f:
        (failed_test_info, passed_test_info) = _findLastPassed(f, module_name, test_name, date)

    return (failed_test_info, passed_test_info)


# returns all the module names present in the HDF5 file
# it will look at multiple file entries to make sure all modules are seen
def getAllModuleNames(hdf5_filename, sandbox, num_files=20):
    with h5py.File(hdf5_filename, libver="latest") as f:
        module_names = _getAllModuleNames(f, sandbox)

    return module_names


# returns all the sandbox names present in the HDF5 file
# will look at multiple file entries to make sure all sandboxes are seen
def getAllSandboxNames(hdf5_filename):
    with h5py.File(hdf5_filename, libver="latest") as f:
        sandbox_names = _getAllSandboxNames(f)

    return sandbox_names


##########################################
# Helper Functions
##########################################


def _getFileKeySandbox(f, sandbox, file_key):
    return f[sandbox][file_key].attrs["filename"].split("/")[-2]


def _getClosestFileKeyToDatetime(f, sandbox, datetime_obj, sandboxes=None):
    # sort the file keys in reverse chronological order (newest entries first)
    sorted_file_keys = sorted(list(f[sandbox].keys()), reverse=True)

    file_key_datetimes = []

    for file_key in sorted_file_keys:
        # if sandboxes is not None:
        #     if _getFileKeySandbox(f, file_key) not in sandboxes:
        #         continue

        try:
            file_key_datetime = datetime.datetime.strptime(file_key, "%Y-%m-%d-%H_%M")
            file_key_datetimes.append(file_key_datetime)
        except Exception as e:
            pass

    closest_datetime = min(file_key_datetimes, key=lambda d: abs(d - datetime_obj))

    # convert datetime back to file key
    return closest_datetime.strftime("%Y-%m-%d-%H_%M")


# internal helper function for the getAllModuleNames utility
def _getAllModuleNames(f, sandbox):
    module_names = []

    # sort the file keys in reverse chronological order (newest entries first)
    sorted_file_keys = sorted(list(f[sandbox].keys()), reverse=True)

    # for i, file_key in enumerate(sorted_file_keys):
    #     # if sandboxes is not None:
    #     #     if _getFileKeySandbox(f, file_key) not in sandboxes:
    #     #         continue

    #     these_module_names = list(f[sandbox][file_key].keys())
    #     module_names.extend(x for x in these_module_names if x not in module_names)

    #     if i > num_files:
    #         break

    return list(f[sandbox][sorted_file_keys[0]].keys())


def _getAllSandboxNames(f):
    return list(f.keys())

    # sandbox_names = []

    # # sort the file keys in reverse chronological order (newest entries first)
    # sorted_file_keys = sorted(list(f[sandbox].keys()), reverse=True)

    # for i, file_key in enumerate(sorted_file_keys):
    #     sandbox_name = _getFileKeySandbox(f, file_key)
    #     if sandbox_name not in sandbox_names:
    #         sandbox_names.append(sandbox_name)

    #     if i > num_files:
    #         break

    # return sorted(sandbox_names)


# internal helper function for the runStats utility
def _runStats(f, sandbox, num_past_runs, date=None):
    run_infos = []

    # sort the file keys in reverse chronological order (newest entries first)
    sorted_file_keys = sorted(list(f[sandbox].keys()), reverse=True)

    if date is not None:
        closest_file_key = _getClosestFileKeyToDatetime(f, sandbox, date)
        sorted_file_keys = [fk for fk in sorted_file_keys if fk <= closest_file_key]

    # iterate through regtests, starting with the newest
    for i, file_key in enumerate(sorted_file_keys):
        # break if we've looked at enough past runs
        if len(run_infos) >= num_past_runs:
            break

        # if sandboxes is not None:
        #     if _getFileKeySandbox(f, sandbox, file_key) not in sandboxes:
        #         continue

        # get and append the info for this module for this regtest
        try:
            run_info = _getRunInfo(f, sandbox, file_key)
            run_infos.append(run_info)
        except Exception as e:
            pass

    # if we haven't found enough test infos in this file, we need to go to previous log files
    if len(run_infos) < num_past_runs:
        # get the previous log file name
        prev_log_filename = _getPrevLogFilename(f.filename)
        # make sure it exists
        if os.path.exists(prev_log_filename):
            with h5py.File(prev_log_filename, "r") as last_f:
                # recursively call _testStats
                run_infos += _runStats(last_f, sandbox, num_past_runs - len(run_infos), date=date)

    return run_infos


# internal helper function for finding module stats for the n most recent runs
def _moduleStats(f, sandbox, module_name, num_past_runs, get_test_infos, date=None):
    module_infos = []

    # sort the file keys in reverse chronological order (newest entries first)
    sorted_file_keys = sorted(list(f[sandbox].keys()), reverse=True)

    if date is not None:
        closest_file_key = _getClosestFileKeyToDatetime(f, sandbox, date)
        sorted_file_keys = [fk for fk in sorted_file_keys if fk <= closest_file_key]

    # iterate through regtests, starting with the newest
    for i, file_key in enumerate(sorted_file_keys):
        # break if we've looked at enough past runs
        if len(module_infos) >= num_past_runs:
            break

        # if sandboxes is not None:
        #     if _getFileKeySandbox(f, file_key) not in sandboxes:
        #         continue

        # get and append the info for this module for this regtest
        try:
            module_info = _getModuleInfo(f, sandbox, file_key, module_name, get_test_infos)
            module_infos.append(module_info)
        except Exception as e:
            pass

        # also break if we've looked at more than 4*num_past_runs (maybe the module is new)
        # otherwise we might end up going through the full HDF5 database
        if i > 4 * num_past_runs:
            break

    # if we haven't found enough test infos in this file, we need to go to previous log files
    if len(module_infos) < num_past_runs:
        # get the previous log file name
        prev_log_filename = _getPrevLogFilename(f.filename)
        # make sure it exists
        if os.path.exists(prev_log_filename):
            with h5py.File(prev_log_filename, "r") as last_f:
                # recursively call _moduleStats
                module_infos += _moduleStats(
                    last_f,
                    sandbox,
                    module_name,
                    num_past_runs - len(module_infos),
                    get_test_infos,
                    date=date,
                )

    return module_infos


# internal helper function for finding test stats for the n most recent runs
def _testStats(f, sandbox, module_name, test_name, num_past_runs, date=None):
    test_infos = []

    # print(test_name)
    # sort the file keys in reverse chronological order (newest entries first)
    sorted_file_keys = sorted(list(f[sandbox].keys()), reverse=True)

    if date is not None:
        closest_file_key = _getClosestFileKeyToDatetime(f, sandbox, date)
        sorted_file_keys = [fk for fk in sorted_file_keys if fk <= closest_file_key]

    # iterate through regtests, starting with the newest
    for i, file_key in enumerate(sorted_file_keys):
        # break if we've looked at enough past runs
        if len(test_infos) >= num_past_runs:
            break

        # if sandboxes is not None:
        #     if _getFileKeySandbox(f, file_key) not in sandboxes:
        #         continue

        # get and append the info for this moule for this regtest
        try:
            test_info = _getTestInfo(f, sandbox, file_key, module_name, test_name)
            test_infos.append(test_info)
            # print(file_key + " : " + str(test_info.passed))
        except Exception as e:
            pass

        # also break if we've looked at more than 4*num_past_runs (maybe the test is new)
        # otherwise we might end up going through the full HDF5 database
        if i > 4 * num_past_runs:
            break

    # if we haven't found enough test infos in this file, we need to go to previous log files
    if len(test_infos) < num_past_runs:
        # get the previous log file name
        prev_log_filename = _getPrevLogFilename(f.filename)
        # make sure it exists
        if os.path.exists(prev_log_filename):
            with h5py.File(prev_log_filename, "r") as last_f:
                # recursively call _testStats
                test_infos += _testStats(
                    last_f,
                    sandbox,
                    module_name,
                    test_name,
                    num_past_runs - len(test_infos),
                    date=date,
                )

    return test_infos


# returns (test_found, passed)
def _checkPassed(f, sandbox, file_key, module_name, test_name):
    # make sure the file name is a valid key
    if sandbox not in list(f.keys()) or file_key not in list(f[sandbox].keys()):
        return (False, False)

    # get the group corresponding to the latest test
    file_group = f[sandbox][file_key]

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


def _getTestInfo(f, sandbox, file_key, module_name, test_name):
    # make sure file_key is a valid key
    if file_key not in list(f[sandbox].keys()):
        raise Exception(f"File key {file_key} not found in HDF5 file")

    # get the module dataset, but make sure it's in this file
    if module_name in list(f[sandbox][file_key].keys()):
        module_dataset = f[sandbox][f"{file_key}/{module_name}"]
    else:
        raise Exception(f"Module {module_name} not found in {f[sandbox][file_key].attrs['filename']}")

    # get the names of the tests - must decode the byte strings
    test_names = np.array([x.decode("ascii") for x in module_dataset["name"]])

    # make sure test is in this module
    if test_name not in test_names:
        raise Exception(f"Test {test_name} not found in {module_name} in {f[sandbox][file_key].attrs['filename']}")

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
        file_key=file_key,
        last_passed_file_key=str(test_row["last_passed_file_key"].astype("U30")),
    )

    return test_info


# returns a ModuleInfo object for a given file key and module name
def _getModuleInfo(f, sandbox, file_key, module_name, get_test_infos=True):
    # make sure file_key is a valid key
    if file_key not in list(f[sandbox].keys()):
        raise Exception(f"File key {file_key} not found in HDF5 file")

    # get the module dataset, but make sure it's in this file
    if module_name in list(f[sandbox][file_key].keys()):
        module_dataset = f[sandbox][f"{file_key}/{module_name}"]
    else:
        raise Exception(f"Module {module_name} not found in {f[sandbox][file_key].attrs['filename']}")

    # get the names of the tests - must decode the byte strings
    test_names = np.array([x.decode("ascii") for x in module_dataset["name"]])

    test_infos = []
    if get_test_infos:
        for test_name in test_names:
            test_infos.append(_getTestInfo(f, sandbox, file_key, module_name, test_name))

    if "elapsed_time" in module_dataset.attrs:
        elapsed_time = module_dataset.attrs["elapsed_time"]
    else:
        elapsed_time = sum(t.elapsed_time for t in test_infos)

    module_info = ModuleInfo(
        name=module_name,
        release=module_dataset.attrs["release"],
        num_tests_ok=module_dataset.attrs["num_successful"],
        num_tests=module_dataset.attrs["num_tests"],
        tests=test_infos,
        start_time=module_dataset.attrs["start_time"],
        elapsed_time=elapsed_time,
    )

    return module_info


# returns a RunInfo object for a given file key
def _getRunInfo(f, sandbox, file_key):
    # make sure file_key is a valid key
    if file_key not in list(f[sandbox].keys()):
        raise Exception(f"File key {file_key} not found in HDF5 file")

    file_group = f[sandbox][file_key]

    run_info = RunInfo(
        filename=file_group.attrs["filename"],
        num_tests_ok=file_group.attrs["num_successful"],
        num_tests=file_group.attrs["num_tests"],
        start_time=file_group.attrs["start_time"],
    )

    return run_info


# assumes file_keys are valid
def _printModuleDiff(f, sandbox, old_file_key, new_file_key):
    old_file_group = f[sandbox][old_file_key]
    new_file_group = f[sandbox][new_file_key]

    # get a list of all modules and their releases
    module_names = list(new_file_group.keys())

    print("Modules changed:")
    for module_name in module_names:
        old_release = old_file_group[module_name].attrs["release"]
        new_release = new_file_group[module_name].attrs["release"]
        if old_release != new_release:
            print(f"\t{module_name}:\t{old_release} -> {new_release}")
        # else:
        #     print(f"No changes in module {module_name}")


# finds the last time a test passed
def _findLastPassed(f, sandbox, module_name, test_name, date=None):
    sorted_file_keys = sorted(list(f[sandbox].keys()), reverse=True)

    if date is not None:
        closest_file_key = _getClosestFileKeyToDatetime(f, sandbox, date)
        sorted_file_keys = [fk for fk in sorted_file_keys if fk <= closest_file_key]

    failed_test_info = None
    passed_test_info = None

    # first check the latest regtests and
    #   1) make sure the module/regtest exist
    #   2) check if the regtest actually failed
    start_file_key_ind = sorted_file_keys[0]
    for regtest_ind, file_key in enumerate(sorted_file_keys):
        (test_found, passed) = _checkPassed(f, sandbox, file_key, module_name, test_name)

        # break out of this loop once we find the test
        # or if we've looked through 20 HDF5 entries and can't find it - then we know that it doesn't exist
        if test_found or regtest_ind > 20:
            start_file_key_ind = regtest_ind
            break

    if not test_found:
        raise Exception(f"Test ({test_name}) or Module ({module_name}) not found!")

    if passed:
        raise Exception(f"{test_name} passed in most recent regtest run!")

    # if we get to here, we know the test exists, and is failing
    # so get the test/module info at this time
    failed_test_info = _getTestInfo(f, sandbox, sorted_file_keys[start_file_key_ind], module_name, test_name)

    last_passed_file_key = failed_test_info.last_passed_file_key
    # if the last_passed_file_key is not nothing, get info for the last time test passed
    # if sandboxes is not None:
    #     while last_passed_file_key != "" and _getFileKeySandbox(f, sandbox, last_passed_file_key) not in sandboxes:
    #         prev_file_key_ind = sorted_file_keys.index(last_passed_file_key) + 1
    #         if prev_file_key_ind >= len(sorted_file_keys):
    #             last_passed_file_key = ""
    #             break

    #         while (
    #             prev_file_key_ind < len(sorted_file_keys)
    #             and _getFileKeySandbox(f, sandbox, sorted_file_keys[prev_file_key_ind]) not in sandboxes
    #         ):
    #             prev_file_key_ind += 1

    #         prev_file_key = sorted_file_keys[prev_file_key_ind]
    #         last_passed_file_key = _getTestInfo(f, sandbox, prev_file_key, module_name, test_name).last_passed_file_key

    # check the last_passed_file_key - if nothing, then we don't have record in the HDF5 file of the test ever passing
    if last_passed_file_key == "":
        raise Exception(f"No record of test {module_name} / {test_name} ever passing!")

    filename = f.filename
    passed_test_info = None
    while os.path.exists(filename):
        try:
            with h5py.File(filename, "r") as last_f:
                passed_test_info = _getTestInfo(last_f, sandbox, last_passed_file_key, module_name, test_name)
                break
        except Exception as e:
            filename = _getPrevLogFilename(filename)

    if passed_test_info is None:
        raise Exception(f"Could not find info for last time the test {module_name} / {test_name} passed!")
    return (failed_test_info, passed_test_info)


# prints all the failed regtests
def _listFailed(f, sandbox, file_key):
    file_group = f[sandbox][file_key]

    num_tabs = 5

    tab_str = "\t" * num_tabs
    print("Failed tests:")
    print(f"\tMODULE{tab_str}TEST")
    print(f"\t------{tab_str}------")
    for module in list(file_group.keys()):
        module_dataset = file_group[module]
        for row in module_dataset:
            row = row.squeeze()
            if row["passed"] == False:
                tab_str = "\t" * (max(0, num_tabs - len(module) // 8))
                print(f"\t{module}{tab_str}{row['name'].astype('U200')}")


# gets the TestInfo objects for all failed tests in a given run
def _getFailedTests(f, sandbox, file_key):
    file_group = f[sandbox][file_key]

    failed_test_infos = []

    for module in list(sorted(file_group.keys())):
        module_dataset = file_group[module]
        for row in module_dataset:
            row = row.squeeze()
            if row["passed"] == False:
                failed_test_infos.append(_getTestInfo(f, sandbox, file_key, module, row["name"].astype("U200")))

    return failed_test_infos


def _getPrevLogFilename(hdf5_filename):
    # split the path based on slashes
    hdf5_path_parts = hdf5_filename.split("/")
    # get just the file name and split it based on periods
    hdf5_filename_parts = hdf5_path_parts[-1].split(".")

    # look for the log index in the file name
    log_index_found = False
    for i, p in enumerate(hdf5_filename_parts):
        try:
            # try to cast the file name part to integer
            num = int(p)
            # if successful, increment the integer
            # e.g. last file name would go from regtest.1.h5 to regtest.2.h5
            hdf5_filename_parts[i] = str(num + 1)
            log_index_found = True
            break
        except ValueError as e:
            pass

    # if we did not find an integer part (i.e. file name is regtest.h5), add one
    # so last file name would become regtest.1.h5
    if not log_index_found:
        hdf5_filename_parts.insert(len(hdf5_filename_parts) - 1, "1")

    # join back the file name parts and the path parts
    last_hdf5_filename = ".".join(hdf5_filename_parts)
    last_hdf5_filename_parts = hdf5_path_parts[:-1] + [last_hdf5_filename]
    last_hdf5_path = "/".join(last_hdf5_filename_parts)

    return last_hdf5_path
