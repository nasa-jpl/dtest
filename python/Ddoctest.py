"""Extends the doctest module with support for small numeric changes.

Author: Christopher Lim (JPL)
Date: 4/12/06

"""

from __future__ import division

from __future__ import absolute_import
from __future__ import print_function

import doctest

from numpy import allclose, count_nonzero
from numpy import array

# Parameters passed to allclose.
# These variables are inserted into the doctest.py module for convenience.
# You can override these from your script.py doctest script
doctest.rtol = 1e-10  # relative error
doctest.atol = 1e-10  # absolute error


class DOutputChecker(doctest.OutputChecker):
    """Our replacement doctest OutputChecker object that uses allclose.

    Also it allows exptected values in the numpy.array() format.

    """

    _diffMessage = ""
    _dictPath = []

    def check_output(self, want, got, optionflags):
        # see if want, got passes default doctest comparison
        if doctest.OutputChecker.check_output(self, want, got, optionflags):
            return True
        # try using numeric comparison via allclose
        try:
            return self.check_allclose(eval(want), eval(got), optionflags)
        except:
            return False

    def check_allclose(self, nwant, ngot, optionflags):
        if isinstance(nwant, dict):
            # have dictionary - compare all the component values
            if not isinstance(ngot, dict):
                print("got value is not a dictionary")
                return False

            extraKeys = set(ngot.keys()).difference(set(nwant.keys()))
            if extraKeys:
                from pprint import pformat

                DOutputChecker._diffMessage = "Got value has additional keys: '%s' in dict\n   %s\n\n" % (
                    list(extraKeys),
                    pformat(ngot),
                )
                return False

            missingKeys = set(nwant.keys()).difference(set(ngot.keys()))
            if missingKeys:
                from pprint import pformat

                DOutputChecker._diffMessage = "Wanted value has additional keys: " "'%s' for got dict\n   %s\n\n" % (
                    list(missingKeys),
                    pformat(ngot),
                )
                return False

            for key in nwant:
                if key not in ngot:
                    DOutputChecker._diffMessage = "Could not find key in got value: %s\n\n" % key
                    return False
                # first compare element as strings using normal doctest
                # comparison
                if not doctest.OutputChecker.check_output(self, str(nwant[key]), str(ngot[key]), optionflags):
                    # now try numeric comparison
                    DOutputChecker._dictPath.append(key)
                    if not self.check_allclose(nwant[key], ngot[key], optionflags):
                        # report failure if any of the key values does
                        # not match
                        return False
            # all component elements match
            return True
        else:
            # not a dictionary
            try:
                status = allclose(ngot, nwant, rtol=doctest.rtol, atol=doctest.atol)
                if not status:
                    path = ""
                    if DOutputChecker._dictPath:
                        path = ".".join(DOutputChecker._dictPath)
                    try:
                        adiff = ngot - nwant
                        if nwant != 0.0:
                            rdiff = (ngot - nwant) / nwant
                        else:
                            rdiff = 1e40
                    except:
                        adiff = array(ngot) - array(nwant)
                        # rdiff = (array(ngot) - array(nwant)) / array(nwant)
                        if count_nonzero(array(nwant)) > 0:
                            rdiff = (array(ngot) - array(nwant)) / array(nwant)
                        else:
                            rdiff = array(ngot) * 1e40

                    # array of flags indicating where abs tolerance is
                    # satisfied
                    abscheck = abs(adiff) < doctest.atol
                    # array of flags indicating where rel tolerance is
                    # satisfied
                    relcheck = abs(rdiff) < doctest.rtol
                    # array of flags indicating where one of abs or rel
                    # tolerance is satisfied
                    combcheck = abscheck + relcheck

                    # gets consistant formatting in Python2/3
                    if isinstance(rdiff, float):
                        rdiff = "%.12g" % rdiff
                    if isinstance(adiff, float):
                        adiff = "%.12g" % adiff

                    DOutputChecker._diffMessage = (
                        "Difference (ngot-nwant) exceeds rtol/atol of "
                        "%g/%g    dictPath='%s'\nreldiff=\n%s\nabsdiff=\n%s\n"
                        "relcheck=\n%s\nabscheck=\n%s\ncombcheck=\n%s\n\n\n"
                        % (
                            doctest.rtol,
                            doctest.atol,
                            path,
                            rdiff,
                            adiff,
                            relcheck,
                            abscheck,
                            combcheck,
                        )
                    )
                    DOutputChecker._dictPath = []
                return status
            except:
                return False

    def output_difference(self, example, got, optionflags):
        """Return a string describing the differences between the expected
        output for a given example (`example`) and the actual output (`got`).

        `optionflags` is the set of option flags used to compare `want`
        and `got`.

        """
        val = doctest.OutputChecker.output_difference(self, example, got, optionflags)
        val += "\n %s\n" % DOutputChecker._diffMessage
        return val


class DDocTestRunner(doctest.DocTestRunner):
    def report_failure(self, out, test, example, got):
        """Report that the given example failed."""
        out(self._failure_header(test, example) + self._checker.output_difference(example, got, self.optionflags))


# taken from doctest.py and modified to use our own DOutputChecker object
def testmod(
    m=None,
    name=None,
    globs=None,
    verbose=None,
    isprivate=None,
    report=True,
    optionflags=0,
    extraglobs=None,
    raise_on_error=False,
    exclude_empty=False,
):
    """Test examples in docstrings in functions and classes reachable from
    module m (or the current module if m is not supplied), starting with
    m.__doc__.

    Unless isprivate is specified, private names
    are not skipped.

    Also test examples reachable from dict m.__test__ if it exists and is
    not None.  m.__test__ maps names to functions, classes and strings;
    function and class docstrings are tested even if the name is private;
    strings are tested directly, as if they were docstrings.

    Return (#failures, #tests).

    See doctest.__doc__ for an overview.

    Optional keyword arg "name" gives the name of the module; by default
    use m.__name__.

    Optional keyword arg "globs" gives a dict to be used as the globals
    when executing examples; by default, use m.__dict__.  A copy of this
    dict is actually used for each docstring, so that each docstring's
    examples start with a clean slate.

    Optional keyword arg "extraglobs" gives a dictionary that should be
    merged into the globals that are used to execute examples.  By
    default, no extra globals are used.  This is new in 2.4.

    Optional keyword arg "verbose" prints lots of stuff if true, prints
    only failures if false; by default, it's true iff "-v" is in sys.argv.

    Optional keyword arg "report" prints a summary at the end when true,
    else prints nothing at the end.  In verbose mode, the summary is
    detailed, else very brief (in fact, empty if all tests passed).

    Optional keyword arg "optionflags" or's together module constants,
    and defaults to 0.  This is new in 2.3.  Possible values (see the
    docs for details):

        DONT_ACCEPT_TRUE_FOR_1
        DONT_ACCEPT_BLANKLINE
        NORMALIZE_WHITESPACE
        ELLIPSIS
        IGNORE_EXCEPTION_DETAIL
        REPORT_UDIFF
        REPORT_CDIFF
        REPORT_NDIFF
        REPORT_ONLY_FIRST_FAILURE

    Optional keyword arg "raise_on_error" raises an exception on the
    first unexpected exception or failure. This allows failures to be
    post-mortem debugged.

    Deprecated in Python 2.4:
    Optional keyword arg "isprivate" specifies a function used to
    determine whether a name is private.  The default function is
    treat all functions as public.  Optionally, "isprivate" can be
    set to doctest.is_private to skip over functions marked as private
    using the underscore naming convention; see its docs for details.

    Advanced tomfoolery:  testmod runs methods of a local instance of
    class doctest.Tester, then merges the results into (or creates)
    global Tester instance doctest.master.  Methods of doctest.master
    can be called directly too, if you want to do something unusual.
    Passing report=0 to testmod is especially useful then, to delay
    displaying a summary.  Invoke doctest.master.summarize(verbose)
    when you're done fiddling.

    """
    # If no module was given, then use __main__.
    if m is None:
        # DWA - m will still be None if this wasn't invoked from the command
        # line, in which case the following TypeError is about as good an error
        # as we should expect
        import sys

        m = sys.modules.get("__main__")

    # Check that we were actually given a module.
    if not doctest.inspect.ismodule(m):
        raise TypeError("testmod: module required; %r" % (m,))

    # If no name was given, then use the module's name.
    if name is None:
        name = m.__name__

    # Find, parse, and run all tests in the given module.
    finder = doctest.DocTestFinder(isprivate, exclude_empty=exclude_empty)

    if raise_on_error:
        runner = doctest.DebugRunner(verbose=verbose, optionflags=optionflags)
    else:
        runner = DDocTestRunner(checker=DOutputChecker(), verbose=verbose, optionflags=optionflags)

    for test in finder.find(m, name, globs=globs, extraglobs=extraglobs):
        runner.run(test)

    if report:
        runner.summarize()

    if doctest.master is None:
        doctest.master = runner
    else:
        doctest.master.merge(runner)

    return runner.failures, runner.tries


# replace doctest's testmod with our own
doctest.testmod = testmod
