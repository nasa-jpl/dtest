"""dtest functions."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import argparse
import contextlib
import datetime
import os
import re
import stat
import subprocess
import sys
import tempfile
import time
import copy
import errno
from Dutils.typing import Tuple, Dict, Any, Literal, List, Self, Optional, Union, Set
from pydantic import BaseModel, model_validator
from functools import cached_property
from enum import Enum

try:
    from multiprocessing import cpu_count, Value

    gpu_mem_usage = Value("l", 0)
except:
    pass

# Try to import Gpu memory functions. Default to setting has_cuda to False.
try:
    from Dtest.DtestGpuMem_Py import getGPUMemTotal, getGPUMemAvailable

    has_cuda = True
    total_gpu_memory = getGPUMemTotal()
except:
    has_cuda = False

from . import killableprocess
from . import TestMagic

try:
    basestring
except NameError:
    basestring = str  # pylint: disable=invalid-name

try:
    raw_input
except NameError:
    raw_input = input


class GPUReservationStatus(Enum):
    SUCCESS = 0
    GPU_NOT_REQUESTED = 1
    TOO_MUCH_MEMORY = 2
    TIMED_OUT = 3
    INVALID_SPECIFICATION = 4


# The log file object.
logfile = []
args_uuid = -1

# The timeout value specified from the command line to override any
# other settings (default or in the config file).
override_timeout = -1

interpolation_data = {}

# Set of already printed deprecation messages.
warning_messages = set()

# true if running multiple tests in parallel
parallel_mode = False


class TestException(Exception):
    """Raised when encountering unresolvable problem during testing."""


def red(message):
    """Print red message to standard error."""
    if sys.stderr.isatty() and os.getenv("TERM") != "dumb":
        red_code = ansi("31m")
        end = ansi("0m")
    else:
        red_code = ""
        end = ""

    print(red_code + message + end, file=sys.stderr)


class BaseArgs(BaseModel):
    """Base class for the parser arguments. This holds common options used by
    all parsers.

    Parameters
    ----------
    log : Optional[str]
        log file name
    append_log : bool
        append log message to an existing logfile; can be set by DTEST_APPENDLOG env variable
    compare : bool
        Just show output diffs of already run tests
    short_summary : bool
        When running in parallel model, only show dots to show progress.
    jobs : int
        Number of jobs to run in parallel. Non-positive values will result in the number of jobs being set to the number of CPUs.
    max_load_saturation : float
        Throttle jobs after reaching this saturation ratio. 1 represents full saturation
    gpu_memory_ratio,
        Only allow jobs to use this ratio of the total GPU memory. 1 represents full GPU memory usage.
    timeout : int
        Timeout value that overrides any default or config file specified TIMEOUT settings. If < 1, then not used.
    scale_timeout : float
        Scale all timeouts by this amount.
    tool : Optional[str]
        Use this tool instead of the default basic test. Options are 'coveragepy', 'memcheck', 'helgrind', 'catchsegv'.
    quarantine : bool
        Run only quarantined tests, which are normally skipped.
    exclude_tags : Set[str]
        Exclude regtest with matching tags (comma separated list of tags).
    run_only_tags: Set[str]
        Run ONLY regtests with matching tags (comma separated list of tags)
    ignore : str
        Ignore tests that match this Unix filename pattern (e.g. "*helgrind*")
    all : bool
        Run regular and quarantined tests (still omit 'skipped' tests)
    fail_fast : bool
        Exit on first error.
    interactive : bool
        Show interactive diffs right after test is run.
    delete: bool
        Delete output files after they pass
    data : Optional[str]
        Generate regtest data output. Specify filename.
    append_data : bool
        Append to the regtest data file (default is False - ie, overwrite file, do not append)
    list_mode : bool
        Simply return list of all test cases that will be run.
    quiet : bool
        Run in quite mode - disable informative messages
    truth_suffix : Union[str, List[str]]
        Use the specified truth file suffix(es) and override the suffix in the DTESTDEFS.cfg files. Specify suffix.
    email_on_failure : bool
        Send email to subscribed addresses upon test failure. Subscription is via EMAIL attribute in DTESTDEFS.cfg.
    prerequisite_imports : Optional[str]
        Refuse to run unless comma-separated imports succeed
    ignore_lock : bool
        Run even if another instance of dtest is running in the same module
    shell : str
        Specify the shell run tests with.
    poll_gpu_memory : bool
        If True, then poll the tests for the GPU memory. This will force the tests to run in serial.
    """

    log: Optional[str]
    append_log: bool
    compare: bool
    short_summary: bool
    jobs: int
    max_load_saturation: float
    gpu_memory_ratio: float
    timeout: int
    scale_timeout: float
    tool: Optional[str]
    quarantine: bool
    exclude_tags: Set[str]
    run_only_tags: Set[str]
    ignore: str
    all: bool
    fail_fast: bool
    interactive: bool
    delete: bool
    data: Optional[str]
    append_data: bool
    list_mode: bool
    quiet: bool
    truth_suffix: Union[str, List[str]]
    email_on_failure: bool
    prerequisite_imports: Optional[str]
    ignore_lock: bool
    shell: str
    poll_gpu_memory: bool

    @model_validator(mode="after")
    def validate(self) -> Self:
        if self.jobs < 0:
            self.jobs = cpu_count()

        if self.poll_gpu_memory:
            # Run jobs in serial if polling the GPU
            self.jobs = 1

        # Ensure exclude_tags and run_only tags are a unique set.
        # Make sure we separate all the comma separated lists into
        # their own tags.
        exclude_tags = set()
        for tag in self.exclude_tags:
            exclude_tags.update(tag.split(","))
        self.exclude_tags = exclude_tags

        run_only_tags = set()
        for tag in self.run_only_tags:
            run_only_tags.update(tag.split(","))
        self.run_only_tags = run_only_tags

        if self.exclude_tags & self.run_only_tags:
            raise ValueError("Cannot specify the same tag in both the '--exclude-tags and --run-only-tags!")

        # Remove "" from truth_suffix if it exists
        if self.truth_suffix == "":
            self.truth_suffix = []
        elif isinstance(self.truth_suffix, list):
            # Filter all instances of "" out of truth suffix. May get more than one if combining.
            self.truth_suffix = list(filter("".__ne__, self.truth_suffix))

        # Set quiet mode to true if list mode is true
        if self.list_mode:
            self.quiet = True

        return self

    @cached_property
    def uuid(self) -> int:
        global args_uuid
        args_uuid += 1
        return args_uuid


class DtestArgs(BaseArgs):
    """Arguments for dtest.

    Parameters
    ----------
    paths : List[str]
        Run subset of tests.
    directory : str
        Directory to run tests from. Can be set by DTEST_TESTDIR env variable.
    """

    paths: List[str]
    directory: str

    @model_validator(mode="before")
    def before_validate(vals: Dict[str, Any]) -> Dict[str, Any]:
        if not vals.get("directory", None):
            vals["directory"] = os.getcwd() if isTestDir(os.getcwd()) else getTopTestDir(os.getcwd())
        return vals

    def __init__(self, **data) -> None:
        super().__init__(**data)
        try:
            if not self.data:
                self.data = os.path.join(self.directory, "regtest.data")

            if not self.log:
                self.log = os.path.join(self.directory, "report")

            self.directory = os.path.abspath(self.directory)
        except TestException as test_exception:
            red(str(test_exception))
            sys.exit(1)

    @cached_property
    def top_test_dir(self) -> str:
        # The top of the test tree
        top_test_directory = getTopTestDir(self.directory)

        try:
            if not getLocalConfig(None, top_test_directory, self.truth_suffix):
                raise TestException("No dtest configuration found at {}".format(top_test_directory))
        except Exception as e:
            raise TestException(f"Issues parsing config at {top_test_directory}. Original exception follows:\n{str(e)}")

        return top_test_directory

    @property
    def run_tests(self) -> bool:
        return not self.compare and not self.list_mode


def baseOptions():
    """Set up command line parser object."""
    parser = argparse.ArgumentParser()

    # register options with the parser object
    parser.add_argument("--log", action="store", nargs=1, help="log file name")

    log_filename = os.getenv("DTEST_LOGFILE")
    parser.set_defaults(log=log_filename)

    parser.add_argument(
        "--append-log",
        "-a",
        action="store_true",
        help="append log message to an existing logfile; can "
        "be set by DTEST_APPENDLOG env variable also "
        "(default: %(default)s)",
    )
    append_log = os.getenv("DTEST_APPENDLOG")
    if append_log is None or append_log == "0":
        append_log = False
    else:
        append_log = True

    parser.set_defaults(append_log=append_log)

    parser.add_argument(
        "--compare",
        "-c",
        action="store_true",
        default=False,
        help="just show output diffs of already run tests " "(default: %(default)s)",
    )

    parser.add_argument(
        "--short-summary",
        action="store_true",
        default=False,
        help="when running in parallel model, only show dots " "to show progress",
    )

    parser.add_argument(
        "--jobs",
        "-j",
        type=int,
        default=1,
        help="number of jobs to run in parallel; non-positive "
        "values will result in the number of jobs being "
        "set to the number of CPUs",
    )

    parser.add_argument(
        "--max-load-saturation",
        type=float,
        default=1.0,
        help="throttle jobs after reaching this saturation "
        "ratio; 1 represents full saturation "
        "(default: %(default)s)",
    )

    parser.add_argument(
        "--gpu-memory-ratio",
        type=float,
        default=0.99,
        help="Only allow jobs to use this ratio of the total GPU memory. 1 represents full GPU memory usage. (default: %(default)s)",
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=-1,
        help="timeout value that overrides any default or " "config file specified TIMEOUT settings",
    )

    parser.add_argument(
        "--scale-timeout",
        type=float,
        default=1.0,
        help="scale all timeouts by this amount",
    )

    parser.add_argument(
        "--tool",
        default=None,
        help="use this tool instead of the default basic test; "
        "options are 'coveragepy', 'memcheck', 'helgrind', 'catchsegv'",
    )

    parser.add_argument(
        "--quarantine",
        action="store_true",
        default=False,
        help="run only quarantined tests, which are normally " "skipped",
    )

    parser.add_argument(
        "--exclude-tags",
        type=str,
        action="append",
        default=[],
        help="Exclude regtest with matching tags (comma separated list of tags)",
    )

    parser.add_argument(
        "--run-only-tags",
        type=str,
        action="append",
        default=[],
        help="Run ONLY regtests with matching tags (comma separated list of tags)",
    )

    parser.add_argument(
        "--ignore",
        default="",
        help="ignore tests that match this Unix filename " 'pattern (e.g. "*helgrind*")',
    )

    parser.add_argument(
        "--all",
        action="store_true",
        default=False,
        help="run regular and quarantined tests (still omit 'skipped' tests)",
    )

    parser.add_argument(
        "--fail-fast",
        action="store_true",
        default=False,
        help="exit on first error",
    )

    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        default=False,
        help="show interactive diffs right after test is run " "(default: %(default)s)",
    )

    parser.add_argument(
        "--no-delete",
        action="store_false",
        dest="delete",
        default=True,
        help="do not delete output files after they pass " "(default: %(default)s)",
    )

    parser.add_argument(
        "--data",
        default=None,
        help="generate regtest data output. Specify filename",
    )

    parser.add_argument(
        "--append-data",
        action="store_true",
        default=False,
        help="append to the regtest data file (default is False - ie, " "overwrite file, do not append)",
    )

    parser.add_argument(
        "--list-mode",
        "-l",
        action="store_true",
        default=False,
        help="simply return list of all test cases that will be run",
    )

    parser.add_argument(
        "--quiet",
        action="store_true",
        default=False,
        help="run in quite mode - disable informative messages",
    )

    parser.add_argument(
        "--truth-suffix",
        type=str,
        nargs="+",
        default="",
        help="use the specified truth file suffix and override the suffix in "
        "the DTESTDEFS.cfg files; specify suffix (default: %(default)s).",
    )

    parser.add_argument(
        "--email-on-failure",
        action="store_true",
        help="send email to subscribed addresses upon test "
        "failure; subscription is via EMAIL attribute in "
        '"DTESTDEFS.cfg"',
    )

    parser.add_argument(
        "--prerequisite-imports",
        help="refuse to run unless comma-separated imports succeed",
    )

    parser.add_argument(
        "--ignore-lock",
        action="store_true",
        help="run even if another instance of dtest is running " "in the same module",
    )

    parser.add_argument("--shell", default="/bin/bash", help="specify the shell run tests with")

    parser.add_argument(
        "--poll-gpu-memory",
        action="store_true",
        help="If specified, then poll the tests for the GPU memory. This will force the tests to run in serial.",
    )

    return parser


def processBaseArgsOptions() -> BaseArgs:
    parser = baseOptions()
    return BaseArgs(**vars(parser.parse_args()))


def processDtestOptions() -> DtestArgs:
    parser = baseOptions()

    parser.add_argument("paths", nargs="*", help="run subset of tests")

    parser.add_argument(
        "--directory",
        "-d",
        default="",
        help="directory to run tests from; can be set by " "DTEST_TESTDIR env variable also (default: %(default)s)",
    )
    testdir = os.getenv("DTEST_TESTDIR")
    parser.set_defaults(directory=testdir)

    return DtestArgs(**vars(parser.parse_args()))


def getModuleName(path):
    """Get the current module name."""
    mod_re = re.compile(r"/(src|Module-Releases)/([^/]+)")
    m = mod_re.search(path)
    if m:
        return m.group(2)
    raise TestException("Unable to determine module name! Current dir: %s" % path)


def applyInterpolations(instr):
    """Interpolates special key words such as YAM_TARGET with actual values.

    Deprecated. Use shell syntax instead.

    """
    outstr = instr
    for key, value in interpolation_data.items():
        if key in outstr and ("$" + key) not in outstr:
            outstr = outstr.replace(key, value)

            warn('"{key}" should be "${key}"; ' "the former is ambiguous; run dtest-upgrade".format(key=key))

    return outstr


def ansi(code):
    """Return escaped color code."""
    return "\x1b[" + code


def warn(message):
    """Print deprecation warning."""
    # Notify user of deprecation on first encounter only.
    if message not in warning_messages:
        red("Warning: {message}".format(message=message))
        warning_messages.add(message)


def getAbsCmp(cp, full_dir):
    """Get the absolute path for the specified comparison program."""
    import shlex

    cplist = shlex.split(cp)
    cpcmd = cplist.pop(0)
    if cpcmd[0] == "/":
        # verify that this is a legal executable
        if not (os.access(cpcmd, os.F_OK) and os.access(cpcmd, os.X_OK)):
            raise TestException('The specified "%s" compare program in %s ' % (cpcmd, cp) + "is not an executable.")
        return cp
    # if relative path, check wrt local directory and convert into a full
    # path
    full_path = os.path.join(full_dir, cpcmd)
    if os.access(full_path, os.F_OK) and os.access(full_path, os.X_OK):
        return " ".join([full_path] + cplist)
    return " ".join([cpcmd] + cplist)


def getLocalConfig(previous_config, full_dir, truth_suffix: Union[str, List[str]]):
    """Parse and load config data from the current directory."""
    config_path = os.path.join(full_dir, "DTESTDEFS.cfg")
    if not os.path.isfile(config_path):
        # Fallback to old naming
        config_path = os.path.join(full_dir, "DTESTDEFS")
        if not os.path.isfile(config_path):
            return previous_config

    # parse the config file
    from . import configobj

    new_config = configobj.ConfigObj(config_path, list_values=True, stringify=False, raise_errors=True)

    # PROCESS LOCAL DATA #################

    # substitute in values for special keys such as YAM_TARGET etc.
    if "RUN" in new_config:
        for cmd, val in new_config["RUN"].items():
            new_config["RUN"][cmd] = applyInterpolations(val)
    elif previous_config and "RUN" in previous_config:
        new_config["RUN"] = previous_config["RUN"]

    # get absolute paths for specified compare & validation routines
    for i in ["COMPARE"]:
        if i in new_config:
            for key, value in new_config[i].items():
                # update the CMP value with the absolute path
                new_config[i][key] = cmpList([applyInterpolations(x) for x in value], full_dir=full_dir)

        elif previous_config and i in previous_config:
            new_config[i] = previous_config[i]

    # MERGE PARENT CONFIG DATA #################

    # get scalar values from parent config and override
    for i in ["TRUTHSUFFIX", "CMP", "TIMEOUT", "ENV", "RESOURCES"]:
        if i not in new_config and previous_config and i in previous_config:
            new_config[i] = previous_config[i]

    # accumulate
    prev_tags = []
    if previous_config:
        prev_tags = previous_config.get("CHILD_TAGS", [])
    if "CHILD_TAGS" not in new_config:
        new_config["CHILD_TAGS"] = prev_tags
    else:
        new_tags = new_config["CHILD_TAGS"]
        if isinstance(new_tags, str):
            new_tags = [new_tags]
        new_config["CHILD_TAGS"] = new_tags + prev_tags

    # export CHILD_TAGS info to the environment so it is available to the test Run
    child_tags = new_config.get("CHILD_TAGS", "")
    if child_tags:
        os.environ["DTEST_CHILD_TAGS"] = ",".join(sorted(child_tags))
    else:
        os.environ["DTEST_CHILD_TAGS"] = ""

    # if no timeout value has been specified in the config files, then
    # use the default value
    if "TIMEOUT" not in new_config:
        # The default process timeout bound in seconds.
        # (Can be overriden by the TIMEOUT variable in DTESTDEFS.cfg)
        default_timeout = 300
        new_config["TIMEOUT"] = str(default_timeout)

    # if a timeout value has been specified on the command line, use it
    if override_timeout > 0:
        new_config["TIMEOUT"] = str(override_timeout)

    # Set the default suffix
    if "TRUTHSUFFIX" not in new_config:
        new_config["TRUTHSUFFIX"] = "orig"

    # if the user has specified the suffix from the command line then
    # use it to override the value in the DTESTDEF.cfg files
    new_config["TRUTHSUFFIX"] = getSuffixes(new_config, additional_suffixes=truth_suffix)

    # set the default compare function
    if "CMP" not in new_config:
        new_config["CMP"] = ["/usr/bin/cmp", "/usr/bin/diff"]
    else:
        # update the CMP value with the absolute path
        if isinstance(new_config["CMP"], basestring):
            new_config["CMP"] = [new_config["CMP"]]
        new_config["CMP"] = cmpList(
            [applyInterpolations(x) for x in new_config["CMP"]],
            full_dir=full_dir,
        )

    if "DELETE" in new_config:
        val = new_config["DELETE"]
        if val == "":
            new_config["DELETE"] = []
        elif not isinstance(val, list):
            new_config["DELETE"] = [val]

    return new_config


def cmpList(value, full_dir):
    """Process compare/validate values into usable values."""
    if not isinstance(value, list):
        value = [value]

    nval = [getAbsCmp(x, full_dir) for x in value]
    if len(nval) == 1:
        nval.append(nval[0])

    return nval


def isTestDir(test_dir):
    """Return True if test_dir is a test directory.

    For example if it matches the 'test-xxx' or 'test_xxx' pattern.

    """
    if not os.path.isdir(test_dir):
        return False

    basename = os.path.basename(test_dir)
    return re.match("test[-_]", basename)


def containsTestDir(test_dir):
    """Return True if test_dir contains any test directories."""
    # Save current directory so that we can restore it afterwards
    try:
        sdirs = os.listdir(test_dir)
    except OSError as exception:
        raise TestException(str(exception))

    result = False
    for i in sdirs:
        if isTestDir(os.path.join(test_dir, i)):
            result = True

    return result


def _isTopDir(startdir):
    """Helper method."""
    parent_dir = os.path.realpath(startdir + "/..")
    status = not containsTestDir(parent_dir)
    return status


def getTopTestDir(path):
    """Return the top level directory for this test directory tree."""
    # First check to make sure we are not already at the top of the module
    if not containsTestDir(path) and not containsTestDir(path + "/.."):
        if os.path.isdir(path + "/test") and containsTestDir(path + "/test"):
            return os.path.realpath(path + "/test")
        if os.path.isdir(path + "/tests") and containsTestDir(path + "/tests"):
            return os.path.realpath(path + "/tests")
        # Who knows where we are!
        raise TestException(
            "Could not find any test directories in the current or one "
            + "level higher directory, and so are unable to determine the main "
            + "test directory! "
            + "Currently at: %s" % path
        )

    # Look for the top
    testdir = path

    while not _isTopDir(testdir):
        # check if the parent is a the top directory
        testdir = testdir + "/.."
    return os.path.realpath(testdir)


def getDefaultConfig(path, truth_suffix: Union[str, List[str]]):
    """Go up the directory tree and get config info from parent directories."""
    # go up one directory and get the default config from there
    parent_dir = os.path.split(path)[0]
    # if the parent_dir matches the "test-" pattern, then get the default
    # directory for it
    if containsTestDir(parent_dir):
        parent_config = getDefaultConfig(parent_dir, truth_suffix)
        new_config = getLocalConfig(parent_config, full_dir=parent_dir, truth_suffix=truth_suffix)
    else:
        new_config = None

    return new_config


def truthFiles(suffixes, full_dir):
    """Return list of truth files in the test directory.
    Returns dictionary of file basenames (keys) corresponding truth
    suffixes (values).
    """

    # Make sure 'suffixes' is a tuple
    if isinstance(suffixes, basestring):
        suffixes = (suffixes,)

    # Get the requested truth files
    truth_files = set()
    for suffix in suffixes:
        truth_files.update([x for x in os.listdir(full_dir) if re.match(".*%s$" % suffix, x)])
    truth_roots = set([os.path.splitext(os.path.basename(x))[0] for x in truth_files])

    # Next get a list of the files with any of the 'truth' suffixes
    orig_files = set()
    for suffix in suffixes:
        orig_files.update([x for x in os.listdir(full_dir) if re.match(".*%s$" % suffix, x)])

    # For each of the valid 'roots', see which suffixed versions exist
    files = {}
    for basename in truth_roots:
        truth_suffixes = []
        for suffix in suffixes:
            filename = os.path.join(full_dir, basename + "." + suffix)
            if os.path.isfile(filename):
                truth_suffixes.append(suffix)
        files[basename] = truth_suffixes

    return files


def runCmd(
    cmd,
    args,
    cwd,
    log_num,
    environment_variables=None,
    timeout=-1,
    shell="/bin/bash",
    output=False,
):  # pylint: disable=unused-argument
    """Run the shell command and return status and return code."""
    fullcmd = [cmd]
    fullcmd.extend(args)
    cmdstr = " ".join(fullcmd)
    curt = time.asctime()
    log(log_num, "* Running '%s' in %s at %s" % (cmdstr, cwd, curt))

    if environment_variables:
        environment_variables = environment_variables.copy()
    else:
        environment_variables = os.environ.copy()

    # Needed to disable spurious ESC characters from being echoed to the
    # output. See: https://bugzilla.redhat.com/show_bug.cgi?id=304181
    environment_variables["TERM"] = "dumb"

    # Note in the env that we are using DTEST.
    environment_variables["DTEST_RUNNING"] = "running"

    # Run tests in non interactive mode.
    environment_variables["DNON_INTERACTIVE"] = "1"

    # Set the DebugLog versobity level to ERROR for running regtests.
    environment_variables["DEBUGLOG_VERBOSITY"] = "ERROR"

    # to get consistent output between C++ and Python print messages
    environment_variables["PYTHONUNBUFFERED"] = "1"

    status = False
    output_file = None
    interrupted = False
    try:
        if not output:
            # For logging to file on error.
            output_file = tempfile.NamedTemporaryFile(prefix="output_", dir=cwd, delete=False)

            os.chmod(output_file.name, 0o664)

        raise ValueError("In general, calling Popen is unsafe, as it can run arbitrary bash commands. Therefore, it has been commented out. To run Dtest, you'll need to uncomment this or replace with something else that can run bash commands listed in DTESTDEFS files.")
        #process = killableprocess.Popen(
        #    # [shell, '-c', cmdstr],
        #    # NOTE: If you re-enable use of 'shell' argument, remove pylint exception above
        #    [cmdstr],
        #    shell=True,
        #    stdin=subprocess.PIPE,
        #    stdout=output_file,
        #    stderr=output_file,
        #    cwd=cwd,
        #    env=environment_variables,
        #    # The default shell is /bin/sh, but we often use bashisms such as >& redirection
        #    executable="/bin/bash",
        #)

        process.stdin.close()

        try:
            return_code = process.wait(timeout)
        except killableprocess.TimeoutExpired as exception:
            return_code = exception
        except KeyboardInterrupt:
            interrupted = True
            process.kill()
            raise
        else:
            if return_code == 0:
                status = True

            if return_code < 0:
                log(log_num, "  Child was terminated by signal %d" % -return_code)
            try:
                # Makes sure any lingering processes in the process group
                # are killed
                process.kill()
            except OSError as e:
                # Handles the case where the process is already dead
                if e.errno != errno.ESRCH:
                    raise
    except OSError as e:
        log(log_num, "  Execution failed: %s" % e)
        return_code = 99999
    finally:
        if output_file:
            output_file.close()

            # Only keeps logs for failed test commands (not comparisons). And
            # do not log if already redirected.
            if status or interrupted or ">&" in cmdstr or args:
                try:
                    os.remove(output_file.name)
                except OSError:
                    pass
            else:
                # Default permission is owner read only.
                try:
                    os.chmod(output_file.name, stat.S_IRUSR | stat.S_IRGRP)
                except OSError:
                    pass

    curt = time.asctime()
    log(log_num, "   Completion status: {}, return_code={} ({})".format(status, return_code, curt))
    return (status, return_code)


def log(log_num: int, value):
    """Log value to the log file."""
    logfile[log_num].write(value + "\n")
    logfile[log_num].flush()


def logTee(log_num: int, value):
    """Log value to the log file AND echo to stdout."""
    log(log_num, value)
    print(value)
    sys.stdout.flush()


def isImageFile(filename):
    """Return True if filename refers to an image file."""
    return "image data" in TestMagic.magicString(filename).lower()


def stripJunk(command):
    """Return the command with Drun and leading whitespace stripped from it."""
    command = command.lstrip()
    if command.startswith("Drun "):
        command = command.replace("Drun", "", 1)
        command = command.lstrip()
    return command


def runUnitTest(
    new_config,
    full_dir,
    root_dir,
    test_command_modifier,
    truth_suffix: Union[str, List[str]],
    log_num,
    shell="/bin/bash",
    delete_output=False,
    gpu_allocation_status=GPUReservationStatus.GPU_NOT_REQUESTED,
):
    """Run the unit test in the directory."""
    start_time = time.time()

    relative_path = full_dir.replace(os.path.commonprefix([full_dir, root_dir]), "").lstrip("/")
    log(log_num, "=========================================")
    logTee(log_num, "Running %s test" % relative_path)
    log(log_num, "=========================================")

    import pprint

    log(log_num, "config=" + pprint.pformat(dict(new_config)))

    if not new_config.get("RUN", {}):
        print(
            """
        No 'RUN' commands have been defined for %s.
        """
            % relative_path
        )
        stats = {
            "sub_tests": {},
            "sub_cmps": {},
            "run": (0, 0),
            "cmp": (0, 0),
            "timed_out": 0,
            "elapsed_time": 0,
        }
        success = 0
        failed = 1
        msg = " STATUS:     RUN: %d/%d   CMP: %d/%d   VAL: %d/%d" % (
            0,
            0,
            0,
            0,
            0,
            0,
        )
        logTee(log_num, msg + "  FAILED !!!")
        return success, failed, stats

    status = True

    environment_variables = os.environ.copy()
    for key, value in new_config.get("ENV", {}).items():
        environment_variables[key] = value

    # if you didn't make a good reservation for the GPU, we won't let you use it
    if gpu_allocation_status != GPUReservationStatus.SUCCESS:
        environment_variables["CUDA_VISIBLE_DEVICES"] = "-1"  # gives 'cudaErrorNoDevice'

        # if the reservation failed (didn't just not request GPU),
        # we will also block access to the display. Tests that need display
        # but no GPU memory are okay since they will use GPU_NOT_REQUESTED
        # automatically by not using GPU_MEM flags
        if gpu_allocation_status != GPUReservationStatus.GPU_NOT_REQUESTED:
            environment_variables["DISPLAY"] = "NotRequested"

    sub_tests = {}
    sub_cmps = {}
    run_success = 0
    timed_out = 0
    run_time_comparison_failures = 0
    for key, cmd in new_config["RUN"].items():
        scmd = stripJunk(cmd)
        if not scmd:
            raise ValueError("Test %s does not a run command defined" % (full_dir))

        cmd = test_command_modifier(stripJunk(cmd), full_dir, logTee)

        # The current command being run (can be used by the test program as
        # a tag, eg. usage info output)
        environment_variables["DTEST_COMMAND"] = key
        environment_variables["DTEST_CURDIR"] = full_dir

        if (
            gpu_allocation_status != GPUReservationStatus.SUCCESS
            and gpu_allocation_status != GPUReservationStatus.GPU_NOT_REQUESTED
        ):
            sys.stderr.write(
                f"Bad gpu memory resource request status: {gpu_allocation_status.name}. Resolve before fixing other errors in this dir.\n"
            )
        #     rstat = False
        #     return_code = 999999
        # else:
        rstat, return_code = runCmd(
            cmd=cmd,
            args=[],
            cwd=full_dir,
            log_num=log_num,
            environment_variables=environment_variables,
            timeout=int(new_config["TIMEOUT"]),
            shell=shell,
        )

        if not isinstance(return_code, int):
            return_code_sub = str(return_code)
        else:
            return_code_sub = return_code

        sub_tests[cmd] = {
            "completion_status": rstat,
            "return_code": return_code_sub,
        }

        if rstat:
            run_success += 1
        else:
            status = False
        if isinstance(return_code, killableprocess.TimeoutExpired):
            timed_out += 1
            # delete_output = False
        elif return_code == 139:
            # Possibly a segfault.
            # delete_output = False
            pass
        elif return_code == 10:
            # This is our custom indicator for comparison failures.
            run_time_comparison_failures += 1
            run_success += 1

        if parallel_mode:
            logTee(log_num, "   %-15s %-15s exit status - %s" % (relative_path, key, rstat))
        else:
            logTee(log_num, "   %-15s exit status - %s" % (key, rstat))

    suffixes = getSuffixes(new_config)
    tfiles = truthFiles(suffixes, full_dir=full_dir)
    # Make a copy to iterate over since we are modifying tfiles as we go
    tfiles_orig = copy.deepcopy(tfiles)

    cmp_success = 0
    cmp_total = len(tfiles) + run_time_comparison_failures
    if "COMPARE" in new_config:
        for pattern, cmd in new_config["COMPARE"].items():
            # make a list of all files matching the specified pattern
            log(log_num, "======")
            log(log_num, "====== COMPARING %s OUTPUT FILES in %s" % (pattern, relative_path))
            log(log_num, "======")

            files = set()
            for filename, truth_suffixes in tfiles_orig.items():

                testable = getTestableFiles(full_dir, filename, truth_suffixes, pattern)
                files.update(testable)

                # Test the testable files
                for fname in testable:
                    num_checked = 0
                    passed = False

                    for suffix in truth_suffixes:
                        # NB: truthFiles has already checked for file validity
                        truth_filename = fname + "." + suffix

                        fullcmd = [cmd[0]]
                        fullcmd.extend([truth_filename, fname])
                        cmdstr = " ".join(fullcmd)

                        # make sure that all truth files have been processed
                        if not os.path.isfile(os.path.join(full_dir, fname)):
                            log(
                                log_num,
                                "  Could not find the "
                                "'%s' output file for the %s truth file." % (fname, truth_filename),
                            )
                            logTee(log_num, "   %-15s missing. comparison  - %s" % (fname, False))
                            # ??? status = False
                            print("asdasd")
                            sub_cmps[cmdstr] = {
                                "completion_status": False,
                                "return_code": "%-15s missing." % (fname),
                            }
                        else:
                            rstat, return_code = runCmd(
                                cmd=cmd[0],
                                args=[truth_filename, fname],
                                cwd=full_dir,
                                log_num=log_num,
                            )

                            if not isinstance(return_code, int):
                                return_code_sub = str(return_code)
                            else:
                                return_code_sub = return_code

                            sub_cmps[cmdstr] = {
                                "completion_status": rstat,
                                "return_code": return_code_sub,
                            }

                            num_checked += 1
                            if rstat:
                                cmp_success += 1
                                passed = True
                                if delete_output:
                                    os.remove(os.path.join(full_dir, fname))
                            else:
                                if num_checked == len(truth_suffixes):
                                    status = False

                            if return_code == -9 and num_checked == len(truth_suffixes):
                                timed_out += 1

                            if passed or num_checked == len(truth_suffixes):
                                if parallel_mode:
                                    logTee(log_num, "   %-15s %-15s comparison  - %s" % (relative_path, fname, rstat))
                                else:
                                    logTee(log_num, "   %-15s comparison  - %s" % (fname, rstat))
                            if passed:
                                break

                # Remove the COMPARE files from the list of files to check
                for fn in files:
                    if fn in tfiles:
                        del tfiles[fn]

    # Process all the remaining truth files
    if tfiles:
        log(log_num, "======")
        log(log_num, "====== COMPARING REMAINING OUTPUT FILES in %s" % relative_path)
        log(log_num, "======")
        cmd = new_config["CMP"]

        for filename, truth_suffixes in tfiles.items():
            num_checked = 0
            passed = False

            for suffix in truth_suffixes:
                # Note that truthFiles has already checked for file validity
                truth_filename = filename + "." + suffix

                fullcmd = [cmd[0]]
                fullcmd.extend([truth_filename, filename])
                cmdstr = " ".join(fullcmd)

                # make sure that all truth files have been processed
                if not os.path.isfile(os.path.join(full_dir, filename)):
                    log(
                        log_num,
                        "  Could not find the " "'%s' output file for the %s truth file." % (filename, truth_filename),
                    )
                    logTee(log_num, "   %-15s missing. comparison  - %s" % (filename, False))
                    status = False
                    sub_cmps[cmdstr] = {
                        "completion_status": False,
                        "return_code": "%-15s missing." % (filename),
                    }
                else:
                    rstat, return_code = runCmd(
                        cmd=cmd[0],
                        args=[truth_filename, filename],
                        cwd=full_dir,
                        log_num=log_num,
                    )

                    if not isinstance(return_code, int):
                        return_code_sub = str(return_code)
                    else:
                        return_code_sub = return_code

                    sub_cmps[cmdstr] = {
                        "completion_status": rstat,
                        "return_code": return_code_sub,
                    }

                    num_checked += 1
                    if rstat:
                        cmp_success += 1
                        passed = True
                        if delete_output:
                            os.remove(os.path.join(full_dir, filename))
                    else:
                        if num_checked == len(truth_suffixes):
                            status = False

                    if return_code == -9 and num_checked == len(truth_suffixes):
                        timed_out += 1

                    if passed or num_checked == len(truth_suffixes):
                        if parallel_mode:
                            logTee(log_num, "   %-15s %-15s comparison  - %s" % (relative_path, filename, rstat))
                        else:
                            logTee(log_num, "   %-15s comparison  - %s" % (filename, rstat))
                    if passed:
                        break

    # Only delete files if there are no errors. The user may want to examine
    # the files in cases of error.
    if status and new_config.get("DELETE", []):
        files = []
        for root, dirs, sfiles in os.walk(full_dir):
            files.extend([os.path.join(root, f) for f in sfiles])
            if ".svn" in dirs:
                dirs.remove(".svn")  # tells walk not to go into the .svn
        log(log_num, "======")
        log(log_num, "====== CLEANING UP IN %s" % relative_path)
        log(log_num, "======")
        for pat in new_config.get("DELETE", []):
            sfiles = [x for x in files if re.match(os.path.join(full_dir, pat), x)]
            log(log_num, "* Deleting %s files matching '%s' pattern" % (sfiles, pat))
            for f in sfiles:
                try:
                    os.remove(f)
                except OSError as os_error:
                    print(os_error)

    # set the success, failed variables
    msg = " STATUS:     RUN: %d/%d   CMP: %d/%d" % (
        run_success,
        len(new_config["RUN"]),
        cmp_success,
        cmp_total,
    )
    if status:
        success = 1
        failed = 0
        logTee(log_num, msg + "  SUCCESS")
    else:
        success = 0
        failed = 1
        logTee(log_num, msg + "  FAILED !!!")
    stats = {
        "sub_tests": sub_tests,
        "sub_cmps": sub_cmps,
        "run": (run_success, len(new_config["RUN"])),
        "cmp": (cmp_success, cmp_total),
        "timed_out": timed_out,
        "elapsed_time": time.time() - start_time,
    }

    return success, failed, stats


def getDiffSelection(new, old, suffixes):
    """Get user's selection of diff type for CHECK mode."""
    val = ""
    suffstr = ""
    if len(suffixes) > 1:
        suffstr = " [suffixes=%s] " % "/".join(suffixes)
    while val not in ["n", "no", "d", "v", "b"]:
        try:
            val = raw_input(
                "\n  Run diff on '%s' and '%s' files%s" % (old, new, suffstr) + "([n]o/[d]iff/[v]isual/[b]oth)? "
            )
        except (EOFError, KeyboardInterrupt):
            sys.stdout.write("\n")
            sys.exit(1)
    return val


def diffAction(new, old, test_name, full_dir):
    """Get user's selection on diff follow up action.

    Returns True if the action is handled and we need to continue.
    Returns False to indicate we need to repeat the compare mode on the
    test.

    """
    val = ""
    while val not in ["n", "no", "y", "yes", "r", "repeat", "s", "soaeigen_update"]:
        try:
            val = raw_input("  Accept '%s' diffs in %s ([y]es/[n]o/[r]epeat/[s]oaeigen_update)? " % (new, test_name))
        except (EOFError, KeyboardInterrupt):
            sys.stdout.write("\n")
            sys.exit(1)

    if val == "y" or val == "yes":
        print("  Replacing '%s' with '%s' ..." % (old, new))
        os.rename(os.path.join(full_dir, new), os.path.join(full_dir, old))
    elif val == "s" or val == "soa_eigen_update":
        # old_orig = old.replace("orig", "orig_soaeigen")
        # print("  Renaming '%s' with '%s' ..." % (old, old_orig))
        # os.rename(os.path.join(full_dir, old), os.path.join(full_dir, old_orig))
        # print("  Replacing '%s' with '%s' ..." % (old, new))
        # os.rename(os.path.join(full_dir, new), os.path.join(full_dir, old))
        old_orig = old + "_soaeigen"
        print(f"  Creating new soaeigen orig file {old_orig}")
        os.rename(os.path.join(full_dir, new), os.path.join(full_dir, old_orig))

        # Try to add the new file to version control.
        try:
            os.system(f"svn add {os.path.join(full_dir, old_orig)}")
        except:
            try:
                os.system(f"git add {os.path.join(full_dir, old_orig)}")
            except:
                print(
                    f'Could not add {os.path.join(full_dir, old_orig)} via "svn add {os.path.join(full_dir, old_orig)}" or "git add {os.path.join(full_dir, old_orig)}"'
                )

    if val == "r" or val == "repeat":
        return False

    return True


def runUnitCmp(new_config, full_dir, root_dir, truth_suffix: Union[str, List[str]], log_num, shell):
    """Run output checks in the unit test in the directory.

    Return False to recycle the checks for the test.

    """
    relative_path = full_dir.replace(os.path.commonprefix([full_dir, root_dir]), "").lstrip("/")
    print("=========================================")
    print("Running output CHECKS in %s test" % relative_path)
    print("=========================================")

    # make a list of all the "orig"
    suffixes = getSuffixes(new_config)
    tfiles = truthFiles(suffixes, full_dir=full_dir)

    # run the validation checks
    if "COMPARE" in new_config:
        for pattern, cmd in new_config["COMPARE"].items():
            # make a list of all files matching the specified pattern
            files = set()

            for filename, truth_suffixes in tfiles.items():
                files.update(getTestableFiles(full_dir, filename, truth_suffixes, pattern))

            for filename in files:
                available_suffixes = []
                for suffix in suffixes:
                    truth_filename = filename + "." + suffix
                    if os.path.isfile(os.path.join(full_dir, truth_filename)) and os.path.isfile(
                        os.path.join(full_dir, filename)
                    ):
                        available_suffixes.append(suffix)
                # print('MMM', filename, available_suffixes)
                for suffix in available_suffixes:
                    # Let user see diffs and potentially update the test
                    truth_filename = filename + "." + suffix
                    if not interactiveDiff(
                        filename=filename,
                        truth_filename=truth_filename,
                        diff_cmds=cmd,
                        test_name=relative_path,
                        full_dir=full_dir,
                        log_num=log_num,
                        shell=shell,
                        suffixes=available_suffixes,
                    ):
                        return False

            # remove the processed files from the list
            for fn in files:
                if fn in tfiles:
                    del tfiles[fn]

    # process all the remaining truth files
    if tfiles:
        cmd = new_config["CMP"]
        for filename in tfiles:
            # handle the case where the fallback '.orig' is used in place of
            # the truth suffix ???
            available_suffixes = []
            for ts in suffixes:
                truth_filename = filename + "." + ts
                if os.path.isfile(os.path.join(full_dir, truth_filename)) and os.path.isfile(
                    os.path.join(full_dir, filename)
                ):
                    available_suffixes.append(ts)

            for ts in available_suffixes:
                truth_filename = filename + "." + ts
                if not interactiveDiff(
                    filename=filename,
                    truth_filename=truth_filename,
                    diff_cmds=cmd,
                    test_name=relative_path,
                    full_dir=full_dir,
                    log_num=log_num,
                    shell=shell,
                    suffixes=available_suffixes,
                ):
                    return False

    return True


def interactiveDiff(filename, truth_filename, diff_cmds, test_name, full_dir, log_num: int, shell, suffixes):
    """Show interactive diffs for the output file.

    Return False if the user wants to recycle the checks for the test.

    """
    if os.path.isfile(os.path.join(full_dir, filename)):
        tkdiff = "tkdiff"

        perceptual_diff = "dtest-perceptual-diff"

        val = getDiffSelection(new=filename, old=truth_filename, suffixes=suffixes)
        if val == "n" or val == "no":
            pass
        elif val == "d":
            # verbose diff
            print("Running '%s %s %s'" % (diff_cmds[1], truth_filename, filename))
            runCmd(
                cmd=diff_cmds[1],
                args=[truth_filename, filename],
                cwd=full_dir,
                log_num=log_num,
                shell=shell,
                output=True,
            )
        elif val == "v":
            # visual diff
            if isImageFile(os.path.join(full_dir, filename)):
                diffcmd = diff_cmds[2] if len(diff_cmds) > 2 else perceptual_diff
                print("Running '%s %s %s'" % (diffcmd, truth_filename, filename))
                runCmd(
                    cmd=diffcmd,
                    args=[truth_filename, filename],
                    cwd=full_dir,
                    log_num=log_num,
                    shell=shell,
                    output=True,
                )
            else:
                diffcmd = diff_cmds[2] if len(diff_cmds) > 2 else tkdiff
                print("Running '%s %s %s'" % (diffcmd, truth_filename, filename))
                runCmd(
                    cmd=diffcmd,
                    args=[truth_filename, filename],
                    cwd=full_dir,
                    log_num=log_num,
                    shell=shell,
                )
        elif val == "b":
            if isImageFile(os.path.join(full_dir, filename)):
                diffcmd = diff_cmds[2] if len(diff_cmds) > 2 else perceptual_diff
                print(
                    "Running '%s %s %s' and '%s %s %s'"
                    % (
                        diff_cmds[1],
                        truth_filename,
                        filename,
                        diffcmd,
                        truth_filename,
                        filename,
                    )
                )
                runCmd(
                    cmd=diffcmd,
                    args=[truth_filename, filename, "&"],
                    cwd=full_dir,
                    log_num=log_num,
                    shell=shell,
                )
            else:
                diffcmd = diff_cmds[2] if len(diff_cmds) > 2 else tkdiff
                print(
                    "Running '%s %s %s' and '%s %s %s'"
                    % (
                        diff_cmds[1],
                        truth_filename,
                        filename,
                        diffcmd,
                        truth_filename,
                        filename,
                    )
                )
                runCmd(
                    cmd=diffcmd,
                    args=[truth_filename, filename, "&"],
                    cwd=full_dir,
                    log_num=log_num,
                )

            runCmd(
                cmd=diff_cmds[1],
                args=[truth_filename, filename],
                cwd=full_dir,
                log_num=log_num,
                shell=shell,
                output=True,
            )
        else:
            raise TestException('Illegal value: "%s"' % val)

        if not diffAction(
            new=filename,
            old=truth_filename,
            test_name=test_name,
            full_dir=full_dir,
        ):
            # the user wants to repeat the checks for this test
            return False

    return True


def getListFromConfig(config, key):
    """Return list with key in config."""
    try:
        return config.as_list(key)
    except KeyError:
        return []


def findTests(
    full_dir: str,
    test_mode: Literal["REGULAR", "QUARANTINE", "ALL"],
    log_num: int,
    exclude_tags: Set[str],
    run_only_tags: Set[str],
    truth_suffix: Union[str, List[str]],
    quiet_mode: bool,
    quarantined: bool = False,
    previous_config: bool = None,
    parallel_mode: bool = False,
):
    """
    Find and generate all test subdirectories.

    Parameters
    ----------
    full_dir : str
        Full directory.
    test_mode : Literal["REGULAR", "QUARANTINE", "ALL"]
        Test mode.
    quarantined : bool
        Whether quarantined.
    previous_config : bool
        The previous test config.
    parallel_mode : bool
        Whether to generate the list in parallel_mode or not. If True, then
        this looks for the "SERIAL" tag in configs, and groups them together
        into a sub-list if True.
    """
    assert test_mode in ("REGULAR", "QUARANTINE", "ALL")

    # If no config has been specified, then we are at the start directory. Get
    # a default config by processing ones in the parent directory tree find.
    if not previous_config:
        previous_config = getDefaultConfig(full_dir, truth_suffix)

    # Load any local config that may exist, or use the ones.
    new_config = getLocalConfig(previous_config, full_dir=full_dir, truth_suffix=truth_suffix)
    if not new_config:
        return

    # Get list of local test directories.
    subtests = set([x for x in os.listdir(full_dir) if isTestDir(os.path.join(full_dir, x))])

    # List of test cases to skip.
    skiptests = getListFromConfig(new_config, "SKIPTESTS")
    # create a list with '/' affixed
    skiptests_suff = [x + "/" for x in skiptests]

    if len(skiptests) == 1 and " test" in skiptests[0]:
        warn("Suspicious space found in SKIPTESTS ({}); " "it should be comma-separated".format(skiptests[0]))

    # List of test quarantined cases to skip
    quarantined_tests = getListFromConfig(new_config, "QUARANTINED")
    # Create a list with '/' affixed.
    quarantined_tests_suff = [x + "/" for x in quarantined_tests]

    if len(quarantined_tests) == 1 and " test" in quarantined_tests_suff[0]:
        warn("Suspicious space found in QUARANTINED ({}); " "it should be comma-separated".format(quarantined_tests[0]))

    if parallel_mode and subtests:
        test_tags = set(getListFromConfig(new_config, "TAGS"))
        if "SERIAL" in test_tags:
            # Rerun this and store the result in a list
            yield [
                t
                for t in findTests(
                    full_dir=full_dir,
                    test_mode=test_mode,
                    log_num=log_num,
                    exclude_tags=exclude_tags,
                    run_only_tags=run_only_tags,
                    truth_suffix=truth_suffix,
                    quiet_mode=quiet_mode,
                    quarantined=quarantined,
                    previous_config=previous_config,
                    parallel_mode=False,
                )
            ]
            return

    # If the list of subtests is non-empty go down the tree.
    if subtests:
        for testdir in sorted(list(subtests)):
            subtest_path = os.path.join(full_dir, testdir)

            if testdir in skiptests or testdir in skiptests_suff:
                if not quiet_mode:
                    logTee(log_num, "Skipping %s test(s)" % subtest_path)
                continue
            else:
                # Quarantined tests only run when dtest is run when
                # quarantine_mode is True.
                # Non-quarantined tests only run when quarantine_mode is False.
                test_is_quarantined = (testdir in quarantined_tests) or (testdir in quarantined_tests_suff)

            if test_is_quarantined and (test_mode == "REGULAR"):
                if not quiet_mode:
                    logTee(log_num, "Skipping quarantined %s test(s)" % subtest_path)
                continue

            # if the test directory is not an immediate
            # sub-directory, then we have to get the configs from
            # the intermediate directories
            if re.match(".*/.", testdir):
                config = getDefaultConfig(subtest_path, truth_suffix)
            else:
                config = new_config

            for t in findTests(
                full_dir=subtest_path,
                test_mode=test_mode,
                log_num=log_num,
                exclude_tags=exclude_tags,
                run_only_tags=run_only_tags,
                truth_suffix=truth_suffix,
                quiet_mode=quiet_mode,
                quarantined=quarantined or test_is_quarantined,
                previous_config=config,
                parallel_mode=parallel_mode,
            ):
                yield t
    else:
        test_tags = set(getListFromConfig(new_config, "TAGS")) | set(getListFromConfig(new_config, "CHILD_TAGS"))

        # Atomic test
        if not quarantined and (test_mode == "QUARANTINE"):
            if not quiet_mode:
                logTee(log_num, "Skipping non-quarantined %s test" % (full_dir,))
            return
        if quarantined and (test_mode == "REGULAR"):
            if not quiet_mode:
                logTee(log_num, "Skipping quarantined %s test" % (full_dir,))
            return
        if "quarantined" in test_tags:
            if not quiet_mode:
                logTee(log_num, "Skipping quarantined %s test  [tag = quarantined]" % (full_dir,))
            return

        # Handle tags

        # Handle the 'skip' tag specially
        if "skip" in test_tags:
            if not quiet_mode:
                logTee(log_num, "Skipping %s test(s)  [tag = skip]" % (full_dir,))
            return

        # Skip the test if any test tags are excluded
        if test_tags & exclude_tags:
            if not quiet_mode:
                etags = ",".join(list(test_tags & exclude_tags))
                logTee(log_num, "Skipping excluded %s test  [tags = %s]" % (full_dir, etags))
            return

        # Handle run-only tags
        if run_only_tags:
            if not test_tags & run_only_tags:
                if not quiet_mode:
                    otags = ",".join(list(run_only_tags))
                    logTee(log_num, "Skipping %s test  [tags %s NOT found]" % (full_dir, otags))
                return

        # No more test sub-directories.
        assert full_dir

        yield full_dir


def dispatchTest(
    full_dir,
    common_directory,
    test_command_modifier,
    truth_suffix: Union[str, List[str]],
    interactive,
    scale_timeout,
    compare_mode,
    gpu_memory_ratio,
    log_num,
    shell="/bin/bash",
    delete_output=True,
) -> Tuple[int, int, Dict[str, Dict[str, Any]]]:
    """Dispatch the tests in the directory."""
    # If no config has been specified, then we are at the start directory. Get
    # a default config by processing ones in the parent directory tree find.
    previous_config = getDefaultConfig(full_dir, truth_suffix)

    # Load any local config that may exist, or use the ones.
    new_config = getLocalConfig(previous_config, full_dir=full_dir, truth_suffix=truth_suffix)
    if not new_config:
        sys.stderr.write("Unable to get test configuration data in {d} directory.".format(d=full_dir))
        return (0, 0, {})

    # No more test sub-directories.
    assert full_dir

    if compare_mode:
        success = 1
        failed = 0
        test_data = {}

        compare(
            new_config=new_config,
            full_dir=full_dir,
            root_dir=common_directory,
            truth_suffix=truth_suffix,
            log_num=log_num,
            shell=shell,
        )
    else:
        new_config["TIMEOUT"] = str(int(scale_timeout * int(new_config["TIMEOUT"])))

        @contextlib.contextmanager
        def awaitGpuMem(gpu_mem_needed: str, timeout: float = 1800.0):
            """This function attempts to wait until the GPU memory is available. This means that:
            1. The amount of memory is avaialable on the physical GPU.
            2. The amount of memory this test will use plus the amount of all the other tests in use is
               less than the totol amount of GPU memory * gpu_memory_ratio.

            If something goes wrong, e.g., the user string was specified
            incorrectly, then we don't bother waiting, but trigger a message to stderr.

            Parameters
            ----------
            gpu_mem_needed : str
                The GPU memory requested by the user via the GPU_MEM section of the config.
            timeout : float
                The amount of time to wait for memory before just trying to continue anyway.
            """

            def processAndAwaitGPUMemory(gpu_mem_needed: str, timeout: float) -> (bool, GPUReservationStatus, int):

                memory_allocated = False

                match = re.search(r"(\d*\.?\d*)\s*([a-z,A-Z]+)?", gpu_mem_needed)
                if match is None:
                    sys.stderr.write(f"The GPU_MEM specification '{gpu_mem}' is invalid for test {full_dir}.")
                    return memory_allocated, GPUReservationStatus.INVALID_SPECIFICATION, 0

                scale = 1.0
                if units := match.groups()[1]:
                    if units.lower() == "kb":
                        scale = 1024
                    elif units.lower() == "mb":
                        scale = 1024**2
                    elif units.lower() == "gb":
                        scale = 1024**3
                    else:
                        sys.stderr.write(f"The GPU_MEM unit specification '{units}' is invalid for test {full_dir}.")
                        return memory_allocated, GPUReservationStatus.INVALID_SPECIFICATION, 0

                # Ensure the graphics card has enough total memory reserved for testing to support this test
                memory_needed = int(float(match.groups()[0]) * scale)
                if memory_needed > total_gpu_memory:
                    sys.stderr.write(
                        f"The desired memory for test {full_dir} is too large. Requested: '{memory_needed}' Total avaiable: '{getGPUMemTotal()}'"
                    )
                    return memory_allocated, GPUReservationStatus.TOO_MUCH_MEMORY, 0

                # Caculate the maximum value the shared_gpu_mem can have based on the ratio
                memory_shared_needed = total_gpu_memory * gpu_memory_ratio - memory_needed
                total_time = 0
                while total_time < timeout:
                    if gpu_mem_usage.value < memory_shared_needed:
                        with gpu_mem_usage.get_lock():
                            # We need to check a second time, since there may have been a race to the lock that we lost.
                            if gpu_mem_usage.value < memory_shared_needed:
                                gpu_mem_usage.value += memory_needed
                                memory_allocated = True
                                break

                    time.sleep(1.0)
                    total_time += 1

                if total_time >= timeout:
                    sys.stderr.write(f"The desired memory for test {full_dir} was not found within {timeout} seconds.")
                    return memory_allocated, GPUReservationStatus.TIMED_OUT, memory_needed

                return memory_allocated, GPUReservationStatus.SUCCESS, memory_needed

            # Flag to determine if we allocated memory or not
            memory_allocated = False

            try:
                memory_allocated, allocation_status, memory_needed = processAndAwaitGPUMemory(gpu_mem_needed, timeout)
                yield allocation_status

            finally:
                if memory_allocated:
                    with gpu_mem_usage.get_lock():
                        gpu_mem_usage.value -= memory_needed

        resources = new_config.get("RESOURCES", {})
        gpu_mem = resources.get("GPU_MEM", None)
        if has_cuda and gpu_mem is not None:
            # GPU_MEM was specified. Check that we have enough available before running the test.
            with awaitGpuMem(gpu_mem) as allocation_status:
                success, failed, stats = runUnitTest(
                    new_config=new_config,
                    full_dir=full_dir,
                    root_dir=common_directory,
                    test_command_modifier=test_command_modifier,
                    truth_suffix=truth_suffix,
                    log_num=log_num,
                    shell=shell,
                    delete_output=delete_output,
                    gpu_allocation_status=allocation_status,
                )
        else:
            success, failed, stats = runUnitTest(
                new_config=new_config,
                full_dir=full_dir,
                root_dir=common_directory,
                test_command_modifier=test_command_modifier,
                truth_suffix=truth_suffix,
                log_num=log_num,
                shell=shell,
                delete_output=delete_output,
            )

        relative_path = full_dir.replace(os.path.commonprefix([full_dir, common_directory]), "").lstrip("/")
        if relative_path == "":
            relative_path = full_dir
        test_data = {
            relative_path: {
                "sub_tests": stats["sub_tests"],
                "sub_cmps": stats["sub_cmps"],
                "success": success,
                "failed": failed,
                "timed_out": 1 if stats["timed_out"] else 0,
                "run": stats["run"],
                "cmp": stats["cmp"],
                "elapsed_time": stats["elapsed_time"],
            }
        }

        # Show interactive diffs if requested.
        if interactive:
            compare(
                new_config=new_config,
                full_dir=full_dir,
                root_dir=common_directory,
                truth_suffix=truth_suffix,
                log_num=log_num,
                shell=shell,
            )
            logTee(log_num, "")

    return (success, failed, test_data)


def compare(new_config, full_dir, root_dir, truth_suffix: Union[str, List[str]], log_num, shell):
    """Run checks for test, and repeat if asked to by the user."""
    status = False
    while not status:
        status = runUnitCmp(
            new_config=new_config,
            full_dir=full_dir,
            root_dir=root_dir,
            truth_suffix=truth_suffix,
            log_num=log_num,
            shell=shell,
        )


def getSuffixes(config, additional_suffixes: Optional[Union[str, List[str]]] = None):
    """Get the suffixes and clean them up if necessary"""
    suffixes = config.get("TRUTHSUFFIX", "orig")

    # Convert string to list
    if isinstance(suffixes, basestring):
        if "," in suffixes:
            suffixes = suffixes.split(",")
        else:
            suffixes = [suffixes]
    elif isinstance(suffixes, tuple):
        suffixes = list(suffixes)

    # Add optional additional suffixes
    if additional_suffixes is not None:
        if isinstance(additional_suffixes, basestring):
            suffixes.append(additional_suffixes)
        else:
            suffixes = suffixes + list(additional_suffixes)

    # Add extra truth extensions from environment variables
    if "DTEST_TRUTH_SUFFIX" in os.environ:
        suffixes.extend(re.split(" *, *| ", os.environ["DTEST_TRUTH_SUFFIX"]))

    # Remove any duplicates
    dupes = set()
    deduped_suffixes = []
    for s in suffixes:
        if s not in dupes:
            dupes.update([s])
            deduped_suffixes.append(s)

    return tuple(deduped_suffixes)


def getTestableFiles(full_dir, filename, truth_suffixes, pattern=None):
    """Get all testable files in full_dir"""
    if pattern:
        matches = set([f for f in os.listdir(full_dir) if re.match(pattern, f)])
    else:
        matches = set([f for f in os.listdir(full_dir)])

    # See if the potential matching files end with a truth suffix
    testable = set()
    for ts in truth_suffixes:
        for f in matches:
            if os.path.isfile(os.path.join(full_dir, f + "." + ts)) and f.startswith(filename):
                testable.update([f])

    return testable


class LockException(Exception):
    """Exception raised when another process has the lock."""

    def __init__(self, lock_filename):
        Exception.__init__(
            self,
            'The existence of "{lock_filename}" indicates that '
            "dtest is currently already running in "
            "this directory\n".format(lock_filename=os.path.relpath(lock_filename, os.getcwd())),
        )


@contextlib.contextmanager
def lock(lock_filename):
    """Yield an exclusive lock on lock_filename.

    Raise a LockException if another process has the lock.

    """
    try:
        timestamp = datetime.datetime.utcfromtimestamp(os.path.getmtime(lock_filename))

        # Remove old locks that are probably invalid. Perhaps dtest got killed
        # forcefully.
        if datetime.datetime.utcnow() - timestamp > datetime.timedelta(hours=1):
            os.remove(lock_filename)
    except OSError:
        pass

    try:
        temporary_file = tempfile.NamedTemporaryFile(dir=os.path.dirname(lock_filename), delete=False)

        temporary_file.write("{pid}\n".format(pid=os.getpid()).encode("utf-8"))
        temporary_file.close()
    except IOError as exception:
        raise TestException(str(exception))

    try:
        # Use os.link() since it is atomic. Merely creating a file would not be
        # atomic and would result in a race condition.
        os.link(temporary_file.name, lock_filename)
    except OSError:
        os.remove(temporary_file.name)
        raise LockException(lock_filename)

    try:
        yield
    finally:
        for name in [lock_filename, temporary_file.name]:
            try:
                os.remove(name)
            except OSError:
                pass
