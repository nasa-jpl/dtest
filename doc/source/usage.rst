.. _Dtest_Usage:

.. index:: Using the Dtest Utilities

.. contents::
   :depth: 2


Using the Dtest Utilities
=========================

Installing Dtest
----------------

In order to install the Dtest utilities, simply include the Dtest module in
the user's sandbox as a work module (directory) or link module and relink.
All necessary executables and libraries will then be usable.

Using the `dtest` test harness
------------------------------

The `dtest` test program can be used in one of three ways:

1. Run `dtest` for an entire sandox.  In the top level of the sandbox, do
   this:

   .. code-block:: sh

       $ gmake regtest

   Note this should work without difficulties for sandboxes where all modules
   are checked out as work modules.  If any modules are link modules, there
   may be issues if the user cannot write test files in the module release
   area.

   Note that this is the way that hourly/overnight regression tests are run:  A
   dedicated all-work sandbox is set up and regression tests and this command
   is executed at the top level to run regtests for all modules.

2. Run `dtest` for a module.  Go to the top level of the module and execute
   this command:

   .. code-block:: sh

      $ gmake -f Makefile.yam regtest


3. Run `dtest` for a set of regression tests.  Go to the level in the test
   hierarchy where you want to run tests and execute this command:

   .. code-block:: sh

      $ <Drun> dtest

   where `dtest` is the Drun executable for this sandbox.  Note that this
   command can be run at any level in the test directory.  It only runs the
   regression tests it finds in the directory in which it is run along with
   any children test directories.


.. index:: Dtest options

Dtest options
-------------

**``Dtest``** accepts several command line options when it is executed
directly.  To specify options, you may give them on the `dtest` command
line:

   .. code-block:: sh

      $ <Drun> dtest <options>

You may see the available options by executing `dtest` with the '--help'
option.


.. index:: Dtest tags

Selective execution of Dtest tests with TAGS (Dtest tags)
---------------------------------------------------------

It is possible to selectively exclude regtests based on the 'TAGS' property
defined in the 'DTESTDEFS' file withing a test sub-directory (but not child
directories). Dtest TAGS offer significant flexibility in controlling the
execution of regression tests.  For instance, if the following tag is defined
in a regtest's DTESTDEFS file:

    TAGS = logging

and `dtest` is executed with the '--exclude-tags' option:

   .. code-block:: sh

      $ <Drun> dtest --exclude-tags logging

then any regtest that defines TAGS to include 'logging' in its DTESTDEFS file
will be excluded (skipped).

You may also run only regtest that contain a specific tag:

   .. code-block:: sh

      $ <Drun> dtest --run-only-tags validation

then only regtests that defines TAGS to include 'validation' in its DTESTDEFS file
will be executed.  Note that all regtests that are marked for skipping or
quarantining, will not be run.

The `dtest` argument `--exclude-tags` can be given multiple times on the
command line and all the exclude tags will be combined.  The `dtest` argument
`--run-only-tags` is handled similarly.

Note that TAGS only affects the subdirectory that it is defined in (in a
DTESTDEFS file).   If you wish to cause all child directories to inherit a
tag, use the CHILD_TAGS property:

    CHILD_TAGS = logging

With this defined, all tests in child directories with get the 'logging' tag
-- as if 'TAGS = logging' was defined in the DTESTDEFS file in all
subdirectories below this directory.

.. note::

    To see a TIM summary presentation on Dtest Tags, please see:

    * :download:`Dtest Tags Presentation (April 2016 TIM) <documents/Dtest-Tags-2016-04-08.pdf>`


Special Dtest tags: skip  and  quarantined
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There are two special tags: **'skip'** and **'quarantined'**.  These do the
same things as listing the regtests in parent DTESTDEFS file 'SKIP' or
'QURANTINED' lists (respectivley).

One advantage in using tagging to skip or quarantine a regtest is that
skip/exclusion flag goes into the same directory as the regtest itself (not
its parent).


Commonly used Dtest tags
~~~~~~~~~~~~~~~~~~~~~~~~

There are several tags that have been defined to provide consistent tagging of tests.
These tags are:

* **'code'**  - Identifies tests that perform code checks.
* **'graphics'** - Identifies tests that use OGRE or other graphics packages that
  might not be available on all platforms.
* **'lcm'** - Identifies tests that use Lightweight Communications and Marshalling (LCM)
  software which might not be available on all platforms.
* **'gtest'** - Identifies tests that use GoogleTest (gtest) software which might not be
  available on all platforms.





Useful Tools for Automated Testing
----------------------------------

JPL provides the following scripts and utilities for automated code testing tasks:

* `Ddoctest`: extends doctest by calling ``numarray.allclose`` so
  numeric differences that fall under a specified tolerance will pass.
  To make existing script.py scripts work, add ``from Dutils import Ddoctest``
  after ``import doctest``.  By default, Ddoctest passes the following parameters
  to ``numarray.allclose``:

    - relative error (stored in ``doctest.rtol``) = 1.0000000000000001e-05
    - absolute error (stored in ``doctest.atol``) = 1e-08

* `compareDictsInFiles`: performs a comparison between
  specially delimited Python dictionaries embedded in text files.

     .. code-block:: sh

         Usage: compareDictsInFiles [options] <dict-file1> <dict-file2>

	 Options:
	  -h, --help           show this help message and exit
          -v, --verbose        Show the diffs.
          --start_re=START_RE  Regular expression immediately before the dictionary (on
                               its own line).  [Default: '<START>'].
          --end_re=END_RE      Regular expression immediately the dictionary (on its
                               own line).  [Default: '<END>'].
          --abs_eps=ABS_EPS    The absolute epsilon to be used in comparisons
                               (defaults to 1.0e-12)
          --rel_eps=REL_EPS    The relative epsilon to be used in comparisons (when
                               numbers are not small, defaults to 1.0e-12)

* `compareCheckpointFiles`: performs a comparison
  between two different checkpoint files.

      .. code-block:: sh

          compareCheckpointFiles [options] <state-file1> <state-file2>

          Options:
            -h, --help     show this help message and exit
            -v, --verbose  Show the diffs.

* `compareModelFiles`: performs a comparison
  between two different model files.

      .. code-block:: sh

          compareModelFiles [options] <model-file1> <model-file2>

          Options:
            -h, --help     show this help message and exit
            -v, --verbose  Show the diffs.

* `genRegtestMail`: takes a regtest.data file
  (the output of a `dtest` run) and constructs and then sends
  emails based on various options.

      .. code-block:: sh

          genRegtestMail [options] -dataFile <regtest data file>

          Options:
            -h, --help            show this help message and exit
            --dataFile=DATAFILE   Regtest data file.
            --title=TITLE         Title to print above the table
            --html                Generate html output to this file
            --url=URL             URL for detailed html results (module name is appended
                                  for each module)
            --moduleOwner=MODULEOWNER
                                  string to be evaluated (or file to be executed) to
                                  construct dictionary:
                                  moduleOwner = {'<module-name>' : '<owner>', ...}
            --file=FILE           file for detailed html results
            --output=OUTPUT       Output file for generated HTML file (defaults to stdout)
            --email=EMAIL         Email address or comma-separated list of emails to
                                  send the summary to. If omitted, print results or
                                  write to output file.

* `genRegtestHtml`: takes a regtest.data file
  (the output of a `dtest` run) and generates an HTML
  formatted status page according to several options.

      .. code-block:: sh

          genRegtestHtml [options] -dataFile <regtest data file>

          Options:
            -h, --help           show this help message and exit
            --dataFile=DATAFILE  Regtest data file.
            --cssURL=CSSURL      Full URL for CSS file
            --title=TITLE        Title for regression test results HTML page.
            --output=OUTPUT      Output file for generated HTML file (defaults to stdout)
            --showVal            Show the VAL outputs for regtests (defaults to False)

* `cmp.prg`: a UNIX shell script for comparing differences between text files.
      White space (and blank lines) are ignored, as well as expected differences,
      which are specified as regular expressions in a separate file.  The first
      command line argument is a Boolean (i.e., "0" or "1") debug flag; when
      enabled, unexpected differences between files are printed to the screen.
      The second argument is the text file containing regular expressions, written
      using the GNU grep syntax; the regular expressions define what text strings
      should match the expected variance between two files, whose names are
      given as the third and fourth arguments respectively.  The script returns
      1 if the files contain unexpected differences, and 0 otherwise.
