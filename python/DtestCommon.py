# Functions that are used by both dtest and dtest-sbox.
# This file is designed to be imported in each of those scripts as follows:
# from Dtest.DtestCommon import *

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import atexit
import contextlib
import datetime
import fnmatch
import getpass
import os
import platform
import pprint
import smtplib
import subprocess
import sys
import time
from functools import reduce

# Try to import Pool if it exists
try:
    from multiprocessing import Pool, cpu_count, Value, get_context
    from multiprocessing.context import ForkServerProcess

    shared_num_active_tests = Value("i", 0)
    failure_count = Value("i", 0)
except:
    pass

# Try to import GPUMemUsage if it exists (which is only if we have cuda)
try:
    from Dtest.DtestGpuMem_Py import getGPUMemUsage
except:
    pass

from Dutils.typing import List, overload, Tuple, Dict, Optional, Any, Union, Generator, Callable, TypeAlias, cast
from Dtest import Test
from Dtest import TestModifiers

if sys.stdout.isatty() and os.getenv("TERM") != "dumb":
    RED = Test.ansi("31m")
    GREEN = Test.ansi("32m")
    BLUE = Test.ansi("34m")
    BOLD = Test.ansi("1m")
    END = Test.ansi("0m")
else:
    RED = ""
    GREEN = ""
    BLUE = ""
    BOLD = ""
    END = ""


def red(text):
    """Return red ANSI-encoded text."""
    return BOLD + RED + text + END


def green(text):
    """Return green ANSI-encoded text."""
    return BOLD + GREEN + text + END


def blue(text):
    """Return blue ANSI-encoded text."""
    return BOLD + BLUE + text + END


def statusOfDisplay():
    """Return DISPLAY string if display is up.

    Otherwise return an empty string.

    """
    try:
        process = subprocess.Popen(["glxinfo"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = process.communicate()[0].decode("utf-8")
    except OSError:
        return ""

    if process.returncode == 0:
        for line in output.split("\n"):
            if line.startswith("name of display:"):
                return line.split(":", 1)[1].strip()
    return ""


def email(to_addresses, subject, body):
    """Send an email."""
    from_address = "{user}@{host}".format(user=getpass.getuser(), host=platform.node())

    message = """From: {from_address}
To: {joined_to_address}
Subject: {subject}

{body}""".format(
        from_address=from_address, joined_to_address=", ".join(list(to_addresses)), subject=subject, body=body
    )

    smtp = smtplib.SMTP(host="smtp.jpl.nasa.gov", port=25)
    try:
        smtp.sendmail(from_addr=from_address, to_addrs=to_addresses, msg=message)
    except smtplib.SMTPException as exception:
        sys.stderr.write("Failed to send email due to {e}".format(e=exception))


def indent(text):
    """Return indented text."""
    return "\n".join([4 * " " + line for line in text.split("\n")])


def shortStatus(value):
    """Only print success/failure."""
    if "FAILED !!!" in value:
        sys.stdout.write(red("F"))
    elif value.startswith("SUMMARY"):
        print("\n")
        print("LLL", value)
        if " 0 failed" in value:
            print(green(value))
        else:
            print(red(value))
    elif "exit status - False" in value or "comparison  - False" in value:
        sys.stdout.write(red("."))
    elif (
        value.lstrip().startswith("STATUS:")
        or "exit status - " in value
        or "comparison  - " in value
        or value.startswith("Running ")
    ):
        sys.stdout.write(".")
    else:
        print(value)
    sys.stdout.flush()


def mediumStatus(value):
    """Only print success/failure along with relative test path info."""
    if "FAILED !!!" in value or value.startswith("Running "):
        pass
        # sys.stdout.write(red('F'))
    elif value.startswith("SUMMARY"):
        if " 0 failed" in value:
            print(green(value))
        else:
            print(red(value))
    elif "exit status - False" in value:
        sys.stdout.write(red(value + "\n"))
    elif "comparison  - False" in value:
        sys.stdout.write(blue(value + "\n"))
    elif value.lstrip().startswith("STATUS:"):
        pass
    elif "exit status - " in value or "comparison  - " in value:
        sys.stdout.write(value + "\n")
    else:
        print(value)
    sys.stdout.flush()


def colorLongStatus(value):
    """Print long status in color."""
    if "FAILED !!!" in value:
        print(red(value))
    elif value.startswith("SUMMARY"):
        print("\n")
        if " 0 failed" in value:
            print(green(value))
        else:
            print(red(value))
    elif "exit status - False" in value or "comparison  - False" in value:
        print(red(value))
    else:
        print(value)


def runTimeError(data):
    """Return True if test result is due to run time failure."""
    status = data["run"]
    if status[0] < status[1]:
        return True
    return False


def failures(results, root_dir):
    """Return a tuple (failed_test_names, failed_test_message)."""
    failure_data = {}
    for r in results:
        if r[1]:
            failure_data.update(r[2])

    all_lines = []
    for name, data in failure_data.items():
        line = os.path.relpath(os.path.join(root_dir, name), os.getcwd())
        if runTimeError(data):
            line = red(line)

        all_lines.append(line)

    return (failure_data.keys(), "\nFailed test(s):\n{}\n".format(indent("\n".join(all_lines))))


class InsaneException(Test.TestException):
    """Raise upon insanity."""


def sanityCheck(args):
    """Make sure dtest scripts are in place."""
    path_variable = os.getenv("PATH")
    if not path_variable:
        # This is nonsense, but we can't really do anything.
        return

    for executable in ["dtest-cram", "dtest-diff", "dtest-numerical-diff"]:
        found = False
        for path in path_variable.split(":"):
            if os.path.exists(os.path.join(path, executable)):
                found = True
                break

        if not found:
            raise InsaneException(
                "Executable {} could not be found; " "dtest is not set up properly".format(executable)
            )

    if args.prerequisite_imports:
        # Run in a subprocess to avoid polluting dtest itself.
        if subprocess.call(["python", "-c", "import " + args.prerequisite_imports]) != 0:
            raise InsaneException('Prerequisite import "{}" failed'.format(args.prerequisite_imports))


def clean(filename):
    """Remove file if it exists."""
    try:
        os.remove(filename)
    except OSError:
        pass


def modifyLogger(base_args: Test.BaseArgs):
    """This function modifies the Test.logTee based on the incoming args.."""
    if base_args.jobs > 1:
        # Multi-line prints get corrupted in multiprocess mode
        def logTee(log_num: int, value):
            """Only print success/failure."""
            Test.log(log_num, value)
            if base_args.short_summary:
                shortStatus(value)
            else:
                mediumStatus(value)

        Test.logTee = logTee
    else:

        def longLogTee(log_num: int, value):
            """Print in color to standard out."""
            Test.log(log_num, value)
            colorLongStatus(value)

        Test.logTee = longLogTee


# Modify nothing by default
def defaultTestModifier(command, *_):
    """Do nothing."""
    return command


def getTestModifier(args):
    if args.tool == "memcheck":
        test_command_modifier = TestModifiers.memcheckModifier
    elif args.tool == "helgrind":
        test_command_modifier = TestModifiers.helgrindModifier
    elif args.tool == "coveragepy":
        test_command_modifier = TestModifiers.pythonCoverageModifier
    elif args.tool == "catchsegv":
        test_command_modifier = TestModifiers.catchsegvModifier
    elif args.tool:
        raise SystemExit('Unknown tool "{}"\n'.format(args.tool))
    else:
        test_command_modifier = defaultTestModifier
    assert test_command_modifier
    return test_command_modifier


def dispatch(dtest_args: Test.DtestArgs, test_command_modifier, full_dir: str):
    sanityCheck(dtest_args)

    return Test.dispatchTest(
        full_dir=full_dir,
        common_directory=dtest_args.directory,
        test_command_modifier=test_command_modifier,
        truth_suffix=dtest_args.truth_suffix,
        interactive=dtest_args.interactive,
        scale_timeout=dtest_args.scale_timeout,
        compare_mode=dtest_args.compare,
        gpu_memory_ratio=dtest_args.gpu_memory_ratio,
        log_num=dtest_args.uuid,
        shell=dtest_args.shell,
        delete_output=dtest_args.delete,
    )


def setupEnvAndLogging(args: Test.DtestArgs):
    """Return test dispatcher."""
    Test.interpolation_data["ROOTDIR"] = args.top_test_dir

    # Start display in background if DISPLAY is set, yet the display is
    # down. Do not run in a subprocess in case other programs need to
    # use the display.
    if 0 and os.getenv("DISPLAY") and os.getenv("DISPLAY") != ":1" and not statusOfDisplay():
        os.system(" ".join(["Xorg", os.getenv("DISPLAY"), "&"]))

    # Set the timeout override value.
    Test.override_timeout = args.timeout

    # Deprecated. Configuration files should be updated to use regular
    # shell syntax instead. For example, "$YAM_TARGET" instead of
    # "YAM_TARGET".
    for i in ["YAM_ROOT", "YAM_TARGET"]:
        nval = os.getenv(i)
        if nval:
            Test.interpolation_data[i] = nval

    Test.logfile.append(None)
    if args.run_tests:
        if args.data and not args.append_data:
            clean(args.data)

        if args.log and not args.append_log:
            clean(args.log)

        sanityCheck(args)

        Test.logfile[args.uuid] = open(args.log, "a" if args.append_log else "w")
    else:
        # Stub out log function.
        Test.log = lambda *_: None


def outputData(args: Test.DtestArgs, test_results, start_time, module_name):
    """Output test results."""
    sanityCheck(args)

    end_time = datetime.datetime.now()

    success = sum([t[0] for t in test_results])
    failed = sum([t[1] for t in test_results])

    extra = " (in {})".format(module_name) if module_name else ""
    Test.logTee(
        args.uuid, "SUMMARY: Ran {} tests, {} succeeded, {} failed{}".format(success + failed, success, failed, extra)
    )

    Test.logTee(args.uuid, "Tests completed in {} seconds".format((end_time - start_time).total_seconds()))

    (failed_test_names, failed_test_message) = failures(test_results, args.directory)

    if failed_test_names:
        Test.logTee(args.uuid, failed_test_message)

    # close the log file
    Test.logfile[args.uuid].close()

    test_data = {}
    for res in test_results:
        test_data.update(res[2])

    if args.data and test_data:
        with open(args.data, "a" if args.append_data else "w") as data_file:
            # Get the end time (approx)
            newdata = {
                module_name: {
                    "root_dir": args.directory,
                    "top_test_dir": args.top_test_dir,
                    "tests": test_data,
                    "display": statusOfDisplay(),
                    "start_time": start_time,
                    "end_time": end_time,
                }
            }

            data_file.write(
                """
import datetime
try:
    regdata
except:
    regdata = {}
""".lstrip()
            )

            data_file.write(
                """
newdata = {new_data}

if len(newdata['{module_name}']['tests']) > 0:
    regdata.update(newdata)
""".format(
                    new_data=pprint.pformat(newdata), module_name=module_name
                ).lstrip()
            )

    if args.email_on_failure and failed:
        email_addresses = Test.getListFromConfig(
            Test.getLocalConfig(None, args.top_test_dir, args.truth_suffix), "EMAIL"
        )

        if email_addresses:
            email(
                to_addresses=email_addresses,
                subject=("[dtest] Test(s) failed in " '"{}"'.format(module_name)),
                body="\n\n\n".join(
                    [
                        failed_test_message.strip(),
                        "Directory:\n" + indent(args.top_test_dir),
                        "Details:\n"
                        + indent(pprint.pformat({k: v for k, v in test_data.items() if k in failed_test_names})),
                    ]
                ),
            )

    return 0 if not failed else 2


NestedStringList: TypeAlias = List[Union[str, "NestedStringList"]]


def flattenNestedStringList(ns: NestedStringList) -> Generator[str, None, None]:
    """Generator that yields all the strings in a NestedStringList."""
    for val in ns:
        if isinstance(val, list):
            yield from flattenNestedStringList(val)
        else:
            yield val


def generateTestList(args: Test.DtestArgs, parallel_mode: bool = False) -> NestedStringList:
    """Return list of tests."""
    # Figure out the test mode
    test_mode = "REGULAR"
    if args.quarantine:
        test_mode = "QUARANTINE"
    if args.all:
        test_mode = "ALL"

    if args.paths:
        base_test_paths = [os.path.realpath(d) for d in args.paths]
    else:
        base_test_paths = [args.directory]

    test_list: NestedStringList = list(
        reduce(
            lambda x, y: list(x) + list(y),
            [
                Test.findTests(
                    full_dir=t,
                    test_mode=test_mode,
                    log_num=args.uuid,
                    exclude_tags=args.exclude_tags,
                    run_only_tags=args.run_only_tags,
                    truth_suffix=args.truth_suffix,
                    quiet_mode=args.quiet,
                    parallel_mode=parallel_mode,
                )
                for t in base_test_paths
            ],
        )
    )

    if parallel_mode:
        # If in parallel mode, sort so that the lists come before
        # the strings. That way, the tests that have to run in
        # serial mode come first. This will reduce the overall
        # testing time.
        def sort_key(val):
            if isinstance(val, str):
                return True
            else:
                return False

        test_list.sort(key=sort_key)

    @overload
    def remove_ignore(t: str) -> Union[str, None]: ...
    @overload
    def remove_ignore(t: NestedStringList) -> NestedStringList: ...
    def remove_ignore(t):
        """
        Remove any tests that match args.ignore
        """
        if isinstance(t, str):
            if not fnmatch.fnmatch(t, args.ignore):
                return t
        else:
            return [v for v in filter(remove_ignore, t)]

    test_list = remove_ignore(test_list)

    return test_list


@contextlib.contextmanager
def dummyLock(_):
    """Dummy lock that does nothing."""
    yield


def loadPerCPU():
    """Return average load divided by CPU count."""
    return os.getloadavg()[0] / cpu_count()


@overload
def run(_args: Test.DtestArgs, dispatch, directory: str) -> Optional[Tuple[int, int, Dict[str, Dict[str, Any]]]]: ...
@overload
def run(
    _args: Test.DtestArgs, dispatch, directory: List[str]
) -> List[Optional[Tuple[int, int, Dict[str, Dict[str, Any]]]]]: ...
def run(_args: Test.DtestArgs, dispatch, directory: Union[str, List[str]]):
    """
    Run test and return results.

    Parameters
    ----------
    directory : Union[str, List[str]]
        Directory list. This can technically also be an arbitrarily nested list of strings, e.g., List[List[str]]

    Returns
    -------
    Optional[Tuple[int, int, Dict[str, Dict[str, Any]]]] | List[Optional[Tuple[int, int, Dict[str, Dict[str, Any]]]]]
        Returns the tests results. The nesting level of the test results will depend on the
        nesting level of the input.
    """

    # Set environment variables for this test
    os.environ["ROOTDIR"] = _args.top_test_dir

    if _args.fail_fast and failure_count.value:
        return (0, 0, {})

    if isinstance(directory, str):
        # Don't launch more than one test at a time if the CPUs are
        # fully utilized
        directory = os.path.join(_args.directory, directory)
        while loadPerCPU() > _args.max_load_saturation and shared_num_active_tests.value >= 1:
            time.sleep(1)

        shared_num_active_tests.value += 1

        try:
            tmp_results = dispatch(full_dir=directory)
            failure_count.value += tmp_results[1]
            return tmp_results
        finally:
            shared_num_active_tests.value -= 1
    else:
        return [run(_args, dispatch, d) for d in directory]


ContainerValue = Tuple[int, int, Dict[str, Dict[str, Any]]]
Container: TypeAlias = Optional[ContainerValue]
NestedContainer: TypeAlias = List[Union[Container, List["NestedContainer"]]]


def runTests(_args: Test.DtestArgs, pool: Union[Pool, None], run: Union[Callable, None]):
    """This function will run the tests in the _args directory. If pool is not None, then
    it will use a map_async to add the tests to the pool. If it is None, then the main thread
    will just run these tests one by one. If pool is defined, then run must be defined. run is
    the function that we will map over when sending jobs to the pool.

    Parameters
    ----------
    _args : Test.DtestArgs
        Args for the tests.
    pool : Union[Pool, None]
        If not None, then this is the multiprocessing pool the jobs will be added to.
        If it is None, then the jobs will be run in serial.
    run : Union[Callable, None]
        This is the function that is mapped over if jobs are being sent to a pool.
    """

    # If poll_gpu_memory, then do that rather than using the regular runner.
    if _args.poll_gpu_memory:
        return getTestMemory(_args)

    # Set up the locker
    if _args.ignore_lock or not _args.run_tests:
        locker = dummyLock
    else:
        locker = Test.lock

    # Get the name of the module being tested
    try:
        module_name = Test.getModuleName(_args.directory)
    except Test.TestException:
        module_name = ""

    # Get the start time (approx)
    _test_start_time = datetime.datetime.now()

    if _args.list_mode:
        _test_list = generateTestList(_args)
        print("\n".join(flattenNestedStringList(_test_list)))
        sys.exit(0)

    try:
        if pool is not None:
            # We are running in parallel and want to add jobs to the pool.

            _test_list = generateTestList(_args, parallel_mode=True)
            if len(_test_list) == 0:
                # No tests were found. Just exit.
                return 0

            # join() will hang if _test_list is empty
            # (http://bugs.python.org/issue12157)
            assert len(_test_list)  # pylint: disable=C1801

            # Process output. Unpack tests that ran in serial.
            def flatten(container: Union[ContainerValue, NestedContainer]) -> Generator[Container, None, None]:
                """
                Flatten the arbitrary list nesting so we have a single level list of Tuples and Nones.
                """
                for i in container:
                    if i is None:
                        yield i
                    elif isinstance(i, int):
                        container = cast(ContainerValue, container)
                        yield container
                        break
                    else:
                        i = cast(NestedContainer, i)
                        yield from flatten(i)

            # We cannot use a "with" context here, since we will return out of this function before
            # the tests are complete. Hence, we enter the context manually, and set triggers to ensure
            # it exits. These triggers are in:
            # * Result callback. If the map_async exits normally.
            # * Error callback. If something happens in the callback.
            # * atexit. This is a catch all in case some error happens that causes both of the first two
            #   triggers to miss.
            lock = locker(os.path.join(_args.top_test_dir, "dtest_lock"))

            # Try to lock. If it fails, just print the exception and return with code 1.
            # Don't exit, as dtest-sbox may encounter this in one module of many.
            try:
                lock.__enter__()
            except Exception as e:
                Test.red(str(e))
                return 1

            exit_lock = lambda: lock.__exit__(None, None, None)
            atexit.register(exit_lock)

            def callback(test_results: NestedContainer):
                """This callback is run using the test results whenever map_async is complete."""
                try:
                    test_results = [t for t in flatten(test_results)]
                    if _args.run_tests:
                        outputData(
                            args=_args, test_results=test_results, start_time=_test_start_time, module_name=module_name
                        )
                except Exception as e:
                    Test.red("Exception in callback")
                    Test.red(str(e))
                exit_lock()

            def error_callback(results):
                """This callback is run if the callback fails."""
                Test.red("Error caused pool to fail, results follow:")
                print(results)
                exit_lock()

            pool.map_async(run, _test_list, callback=callback, error_callback=error_callback)
            return 0
        else:
            # We are running tests in serial

            # Set environment variables for the test(s)
            os.environ["ROOTDIR"] = _args.top_test_dir

            with locker(os.path.join(_args.top_test_dir, "dtest_lock")):
                # This must run before longLogTee or the test list, as it may change Test.log, and is also used
                # to create the logfile.
                setupEnvAndLogging(_args)

                # Get the test command modifier
                test_command_modifier = getTestModifier(_args)

                # running in serial mode
                _test_list = generateTestList(_args)

                # This is a list so that it can be mutated
                failure_count = [0]

                def runSingleProcess(directory):
                    """Run in single process mode."""
                    if _args.fail_fast and failure_count[0]:
                        return (0, 0, {})
                    _tmp_results = dispatch(_args, test_command_modifier, full_dir=directory)
                    failure_count[0] += _tmp_results[1]
                    return _tmp_results

                _test_results = [runSingleProcess(_t) for _t in _test_list]

                if _args.run_tests:
                    return outputData(
                        args=_args, test_results=_test_results, start_time=_test_start_time, module_name=module_name
                    )
                else:
                    return 0
    except Test.LockException as lock_exception:
        Test.red(str(lock_exception))
        sys.exit(1)
    except Test.TestException as test_exception:
        Test.red(str(test_exception))
        sys.exit(1)


# Start separate thread to poll the GPU
def pollGpu(stop, result_queue):
    """This function polls the gpu until stop is set. Then, it takes the
    maximum value it got during the poll and puts it on the result queue."""
    gpu_start = getGPUMemUsage()
    max_gpu_usage = 0

    # Continuously poll the GPU for the current usage.
    while not stop.is_set():
        gpu_usage = getGPUMemUsage() - gpu_start
        if gpu_usage > max_gpu_usage:
            max_gpu_usage = gpu_usage

    result_queue.put(max_gpu_usage)


class PollGPU:
    """Class to poll the GPU. It has a context to start/stop polling."""

    def __init__(self):
        self.gpu_usage: float = 0.0
        self._context = get_context("forkserver")
        self.result_queue = self._context.Queue()
        self.stop_event = self._context.Event()
        self.process: Optional[ForkServerProcess] = None

    def __enter__(self):
        # Reset the gpu_usage
        self.gpu_usage = 0.0

        # Reset the stop event and process
        self.stop_event.clear()
        self.process = None

        self.process = self._context.Process(target=pollGpu, args=(self.stop_event, self.result_queue))
        self.process.start()

    def __exit__(self, *_):
        # Stop polling
        self.stop_event.set()
        if self.process is not None:
            self.process.join()
        self.gpu_usage = self.result_queue.get()


def getTestMemory(_args: Test.DtestArgs):
    """This function will run the tests in the _args directory. For each test,
    it will poll the GPU memory and keep track of how much was used.

    Parameters
    ----------
    _args : Test.DtestArgs
        Args for the tests.
    """
    # Set up the locker
    if _args.ignore_lock or not _args.run_tests:
        locker = dummyLock
    else:
        locker = Test.lock

    # Get the start time (approx)
    _test_start_time = datetime.datetime.now()

    # Get the name of the module being tested
    try:
        module_name = Test.getModuleName(_args.directory)
    except Test.TestException:
        module_name = ""

    try:
        # We are running tests in serial
        # Set environment variables for the test(s)
        os.environ["ROOTDIR"] = _args.top_test_dir

        with locker(os.path.join(_args.top_test_dir, "dtest_lock")):
            # This must run before longLogTee or the test list, as it may change Test.log, and is also used
            # to create the logfile.
            setupEnvAndLogging(_args)

            # Get the test command modifier
            test_command_modifier = getTestModifier(_args)

            # running in serial mode
            _test_list = generateTestList(_args)

            # This is a list so that it can be mutated
            failure_count = [0]

            # Create GPU poller
            poll_gpu = PollGPU()

            def runSingleProcess(directory):
                """Run in single process mode."""
                if _args.fail_fast and failure_count[0]:
                    return (0, 0, {})
                with poll_gpu:
                    _tmp_results = dispatch(_args, test_command_modifier, full_dir=directory)
                test_data = _tmp_results[2]
                if len(test_data) > 0:
                    test_data[list(test_data.keys())[0]].update({"gpu_usage": poll_gpu.gpu_usage})
                failure_count[0] += _tmp_results[1]
                return _tmp_results

            _test_results = [runSingleProcess(_t) for _t in _test_list]

            if _args.run_tests:
                return outputData(
                    args=_args, test_results=_test_results, start_time=_test_start_time, module_name=module_name
                )
            else:
                return 0
    except Test.LockException as lock_exception:
        Test.red(str(lock_exception))
        sys.exit(1)
    except Test.TestException as test_exception:
        Test.red(str(test_exception))
        sys.exit(1)
