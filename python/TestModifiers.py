"""Functions that modify the basic dtest test commands to do something else.

Test command modifiers take the default test command and modifies it to
create a totally different kind of test (coverage, memory check, etc.).

"""

from __future__ import division

from __future__ import absolute_import
from __future__ import print_function

import os

from . import TestMagic


def isPythonFile(filename):
    """Return True if filename points to a Python file."""
    if not os.path.exists(filename):
        return False
    # Magic doesn't detect files as Python if they use the !/bin/sh hack that
    # we use in our executable Python files (unless there is modeline for
    # Python).
    # We will add the following check as a workaround.
    if filename.endswith(".py") or filename.endswith("Py"):
        return True
    return "python" in TestMagic.magicString(filename).lower()


def pythonCoverageModifier(command, directory, log_function):
    """Return a coverage.py command to do a Python coverage test."""
    # Run using 'coverage' if this is a Python-based test.
    split_command = command.split()
    python_command = None
    if split_command[0] == "python":
        python_command = command.replace("python", "", 1)
    elif isPythonFile(os.path.join(directory, split_command[0])):
        python_command = command
    elif isPythonFile("{0}/bin/{1}".format(os.getenv("YAM_ROOT"), split_command[0])):
        python_command = "%s/bin/%s" % (os.getenv("YAM_ROOT"), command)

    if python_command:
        command = "coverage run --parallel-mode --branch " + python_command
        log_function("Running modified command for Python coverage: " + command)

    return command


def sanitizedFilename(input_string):
    """Returns a modified version of a string that is sanitized to be a valid
    filename."""
    input_string = input_string.replace(" ", "_")
    input_string = input_string.replace("/", "_")
    import string

    valid_characters = "-_%s%s" % (string.ascii_letters, string.digits)
    return "".join(c for c in input_string if c in valid_characters)


def memcheckModifier(command, directory, log_function):
    """Modifies binary-based tests to be run under Valgrind's memcheck tool."""
    magic_string = TestMagic.magicString(os.path.join(directory, command.split()[0]))
    if command.startswith("valgrind"):
        return command
    if "ELF" in magic_string and "executable" in magic_string:
        # We have to specify an error exit code to have valgrind indicate error
        # through it.
        modified_command = (
            "valgrind --tool=memcheck --error-exitcode=77 --leak-check=full "
            "--quiet --log-file={memcheck_log}.memcheck.log {command}".format(
                memcheck_log=sanitizedFilename(command), command=command
            )
        )
        log_function("Running modified command for memcheck: " + modified_command)
        return modified_command
    return command


def helgrindModifier(command, directory, log_function):
    """Modifies binary-based tests to be run under Valgrind's helgrind tool."""
    magic_string = TestMagic.magicString(os.path.join(directory, command.split()[0]))
    if command.startswith("valgrind"):
        return command
    if "ELF" in magic_string and "executable" in magic_string:
        # We have to specify an error exit code to have valgrind indicate error
        # through it.
        modified_command = (
            "valgrind --tool=helgrind --error-exitcode=77 --quiet "
            "--log-file={helgrind_log}.helgrind.log {command}".format(
                helgrind_log=sanitizedFilename(command), command=command
            )
        )
        log_function("Running modified command for helgrind: " + modified_command)
        return modified_command
    return command


def catchsegvModifier(command, directory, _):
    """Modifies binary-based tests to be run under catchsegv.

    Use libsegfault_catcher.so if available.

    """
    split_command = command.split()
    if command.startswith("catchsegv"):
        return command

    magic_string = TestMagic.magicString(os.path.join(directory, split_command[0]))

    segfault_catcher = getSegfaultCatcher()
    if segfault_catcher:
        modified_command = "LD_PRELOAD='{}' {}".format(segfault_catcher, command)
    else:
        modified_command = "catchsegv {}".format(command)

    if "ELF" in magic_string and "executable" in magic_string:
        return modified_command
    if split_command[0] == "python":
        return modified_command
    if isPythonFile(os.path.join(directory, split_command[0])):
        return modified_command
    if isPythonFile("{0}/bin/{1}".format(os.getenv("YAM_ROOT"), split_command[0])):
        return modified_command

    return command


def getSegfaultCatcher():
    """Return libsegfault_catcher.so.

    Return None if not found.

    """
    for path in os.getenv("LD_LIBRARY_PATH", "").split(":"):
        candidate = os.path.join(path, "libsegfault_catcher.so")
        if os.path.exists(candidate):
            return candidate

    return None
