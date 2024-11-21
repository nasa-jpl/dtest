r"""Simple test harness

Synopsis:

  from Dtest.TestUtils import confirm,finish

  result = do_stuff()
  confirm( result, msg = 'do_stuff() succeeded')

  x = compute_thing()
  confirm_equal( x, x_reference, msg = 'x has expected value')

  finish()

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


import sys
import re
from inspect import currentframe

import numpy as np

Nchecks = 0  # (allow invalid var name) pylint: disable=C0103
NchecksFailed = 0  # (allow invalid var name) pylint: disable=C0103

# no line breaks. Useful for test reporting. Yes, this sets global state, but
# we're running a test harness. This is fine
np.set_printoptions(linewidth=1e10, suppress=True)

# I want to 'from termcolor import colored', but the DARTS machines don't have
# this module, so I implement what I want myself


def print_red(x):
    """print the message in red"""
    sys.stdout.write("\x1b[31m" + x + "\x1b[0m\n")


def print_green(x):
    """Print the message in green"""
    sys.stdout.write("\x1b[32m" + x + "\x1b[0m\n")


def error_linenos():
    r"""Returns a useful "current" line number

    I want to tell the user where the error occurred, but for it to be useful,
    this shouldn't be inside the testing infrastructure. I rewind the stack
    until I hit a non-testing frame
    """

    # I report all frames until I find one that isn't in a "confirm_" function.
    # This allows us to ignore helper confirm_ functions when reporting an error
    # line number
    frame = currentframe().f_back.f_back
    out = [frame.f_lineno]

    while frame:
        if frame.f_back is None or not re.match("confirm", frame.f_code.co_name):
            break
        frame = frame.f_back
        out.append(frame.f_lineno)

    if len(out) == 1:
        return out[0]

    return str(out)


def confirm_equal(x, xref, msg="", eps=1e-6):
    r"""If x is equal to xref, report test success.

    msg identifies this check. eps sets the equality tolerance. The x,xref
    arguments can be given as many different types. This function tries to do
    the right thing.

    """

    global Nchecks  # (allow invalid var name, global) pylint: disable=C0103,W0603
    global NchecksFailed  # (allow invalid var name, global) pylint: disable=C0103,W0603
    Nchecks = Nchecks + 1

    # strip all trailing whitespace in each line, in case these are strings
    if isinstance(x, str):
        x = re.sub("[ \t]+(\n|$)", "\\1", x)
    if isinstance(xref, str):
        xref = re.sub("[ \t]+(\n|$)", "\\1", xref)

    # convert data to numpy if possible
    try:
        xref = np.array(xref)
    except:
        pass
    try:
        x = np.array(x)
    except:
        pass

    try:  # flatten array if possible
        x = x.ravel()
        xref = xref.ravel()
    except:
        pass

    try:
        N = x.shape[0]  # (allow short var name) pylint: disable=C0103
    except:
        N = 1  # (allow short var name) pylint: disable=C0103
    try:
        Nref = xref.shape[0]  # (allow invalid var name) pylint: disable=C0103
    except:
        Nref = 1  # (allow invalid var name) pylint: disable=C0103

    if N != Nref:

        print_red(
            (
                "FAILED{} at line {}: mismatched array sizes: N = {} but Nref = {}. Arrays: \n"
                + "x = {}\n"
                + "xref = {}"
            ).format(": " + msg if msg else "", error_linenos(), N, Nref, x, xref)
        )
        NchecksFailed = NchecksFailed + 1
        return False

    if N != 0:
        try:  # Can I subtract?
            x - xref  # (allow statement with no effect) pylint: disable=W0104

            def norm2sq(x):
                """Return 2 norm"""
                return np.inner(x, x)

            rms = np.sqrt(norm2sq(x - xref) / N)
            if not np.all(np.isfinite(rms)):
                print_red(
                    "FAILED{} at line {}: Some comparison results are NaN or Inf. "
                    "rms error = {}. x = {}, xref = {}".format(": " + msg if msg else "", error_linenos(), rms, x, xref)
                )
                NchecksFailed = NchecksFailed + 1
                return False
            if rms > eps:
                print_red(
                    "FAILED{} at line {}: rms error = {}.\nx,xref,err =\n{}".format(
                        ": " + msg if msg else "",
                        error_linenos(),
                        rms,
                        np.vstack((x, xref, x - xref)).transpose(),
                    )
                )
                NchecksFailed = NchecksFailed + 1
                return False
        except:  # Can't subtract. Do == instead
            if not np.array_equal(x, xref):
                print_red(
                    "FAILED{} at line {}: x =\n'{}', xref =\n'{}'".format(
                        ": " + msg if msg else "", error_linenos(), x, xref
                    )
                )
                NchecksFailed = NchecksFailed + 1
                return False
    print_green("OK{}".format(": " + msg if msg else ""))
    return True


def confirm(x, msg=""):
    r"""If x is true, report test success.

    msg identifies this check"""

    global Nchecks  # (allow invalid var name, global) pylint: disable=C0103,W0603
    global NchecksFailed  # (allow invalid var name, global) pylint: disable=C0103,W0603
    Nchecks = Nchecks + 1

    if not x:
        print_red("FAILED{} at line {}".format(": " + msg if msg else "", error_linenos()))
        NchecksFailed = NchecksFailed + 1
        return False
    print_green("OK{}".format(": " + msg if msg else ""))
    return True


def finish():
    r"""Finalize the executed tests.

    Prints the test summary. Exits successfully iff all the tests passed.

    """
    if not Nchecks and not NchecksFailed:
        print_red("No tests defined")
        sys.exit(0)

    if NchecksFailed:
        print_red("Some tests failed: {} out of {}".format(NchecksFailed, Nchecks))
        sys.exit(1)

    print_green("All tests passed: {} total".format(Nchecks))
    sys.exit(0)
