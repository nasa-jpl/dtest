.. _Dtest_Testing:

.. index:: JPL Darts/Dshell Testing Framework

JPL Darts/Dshell Testing Framework
==================================

Dartslab Regression Testing
---------------------------
* Hourly, Daily, and Release-driven Builds
* Currently over 500 regression tests
* Sandboxes used for testing
    - Source
    - Link
* Test mechanism
    - Python doctest
    - Arbitrary scripts
* Testing Reporting
    - Email
    - Website


The Darts/Dshell `dtest` Testing Harness
----------------------------------------
* Modules can run `'gmake -f Makefile.yam regtest'` to run all regression tests in the module
* Runs all tests in a specified test directory and all sub-directories (recursively)
    - Runs in directories that match the ``test_*`` file name pattern (the older ``test-*``
      format is still supported, but developers are encouraged to use the new "underscore"
      naming convention).
* 'dtest' uses a configuration file: DTESTDEFS
    - DTESTDEFS files use the *configObj* format (a super set of Windows .ini files)
    - Define test command(s) for sub-directories
         + Can be an arbitrary command (run executable, run python script, etc)
         + Define where output results go (for comparison tests)
    - Define how to do comparisons
    - Define any cleanup procedures
    - Each test directory can override any parent configuration information with its
      own DTESTDEFS file (e.g., run multiple and/or specialized tests in the directory)


Typical Testing Directory Structure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
::

    |-- DTESTDEFS
    |-- test_basic
    |   |-- graphics.py
    |   |-- test_algmbody
    |   |   |-- model.py
    |   |   |-- output.orig
    |   |   `-- script.py
    |   |-- test_rigidbody
    |   |   |-- test_tumbling
    |   |   |   |-- DTESTDEFS
    |   |   |   |-- model.py
    |   |   |   |-- output.orig
    |   |   |   |-- outputEulerSemiImplicit.orig
    |   |   |   |-- script.py
    |   |   |   `-- scriptEulerSemiImplicit.py
    . . . . . snip . . . . . . . . . . . . . . .
    |   |   `-- utils.py
    |   `-- test_subgraphs
    |       |-- model.py
    |       |-- output.orig
    |       `-- script.py
    `-- test_shapes
        |-- test_cylinder2D
        |   |-- output.orig
        |   |-- script.m
        |   `-- script.py
        `-- test_torus2D
            |-- output.orig
            |-- script.m
            `-- script.py

NOTES:
 * Nested test directories
 * Base DTESTDEFS file defines defaults for all tests
 * DTESTDEFS files in sub-directories
 * DTESTDEFS files in individual test directories can override any
   higher-level defaults, as seen in the above layout of the
   ``test_tumbling`` directory structure.
 * Each test sub-directory has complete control over how its test works using
   its own DTESTDEFS file.


Sample DTESTDEFS file
~~~~~~~~~~~~~~~~~~~~~
::

    # comma separated list of tests to skip
    SKIPTESTS = test_func1, test_func2

    # file suffix for the "known good" comparison file
    TRUTHSUFFIX = orig

    # "debris" files to be deleted after the test
    DELETE=.*\.pyc

    # the default comparison program and options
    CMP = cmp.prg 0, cmp.prg 1

    [COMPARE]

      model.out$ = compareModelFiles, /usr/bin/diff

    [RUN]

      cmd1 = python script.py >& output
      cmd2 = python script2.py >& output2

NOTES:
   * Files with the designated "truth" suffix are used to determine correctness of the run.
   * Custom comparison programs can be specified (e.g., the system's `diff` utility)
   * Comparisons can be defined in the [COMPARE] section as shown above, or alternatively,
     a custom comparison operation can be performed as part of the test command in the
     [RUN] section.  Keep in mind that individual tests are free to override the default
     options for the comparison utility.


Running `dtest` in a test directory
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* `dtest` reads local DTESTDEFS file (if any)
* `dtest` runs all the test commands
* Check for test failures (error return status)
* Compare output files with the known "truth" output (e.g., manually verified,
  standard data set, etc)
  - If any of the comparisons fail, then the entire test fails
* Delete any debris files (as defined in DTESTDEFS)
* Save test results into the `regtest.data` text file.  This output
  file can be analyzed at a later time with automated tools (see :doc:`usage`).


Testing Flexibility with `dtest`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Tests can be completely user-defined
* Output files that will be compared with "truth" versions can be redirected
  from standard output or created in any manner by the test (e.g., image files)
* We have comparison scripts that take lists of regexps to ignore superfluous
  differences (e.g., file paths)
* We sometimes do specialized file comparisons as tests themselves to do "fuzzy" tests
* Tests that are obsolete can be skipped by the DTESTDEFS file
