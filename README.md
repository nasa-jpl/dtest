---
title: dtest
---

Unit testing tool used by JPL's DARTS (Dynamic Algorithms for Real-Time Simulation) software.

# Usage

To run dtest in a module already setup for testing:

    $ srun dtest

# Installation

In order to use the Dtest testing utiltities (dtest,
compareCheckpointFiles, etc.), Dtest should be included as a module
(directory) in the user\'s sandbox. See the module documentation for
further usage suggestions.

# Configuration

Each root test directory should have a `DTESTDEFS.cfg` files. It should
have `CMP` parameter, which should be a comparison (diff) command:

    CMP=dtest-diff 0 $ROOTDIR/common/regexp.lst

If there is a verbose mode for that command, add it to the CMP as a
second value (separated by a comma):

    CMP=dtest-diff 0 $ROOTDIR/common/regexp.lst,dtest-diff 1 $ROOTDIR/common/regexp.lst

Tests should go under the `[RUN]` section. Each test should have a
unique name:

    [RUN]

    test=python script.py >& output
    foo=./bar

If you don\'t care about comparing output, you can leave out the output
redirection. If the output is not redirected to file, dtest will be
automatically pipe it to a temporary file. That temporary file will be
left around only if the test fails (for purposes of examination by the
user).

dtest will look for any files that end with `.orig` and compare it with
the (newly) outputted file with the similar prefix. For example, if
`foo.orig` exists, dtest will compare it with `foo`.

# Upgrading old configuration files

Previous versions of dtest accepted `ROOTDIR` and `YAM_TARGET` keywords
to be specified in the test configuration files without leading `$`.
This is now deperecated. This can be upgraded via a script:

    $ srun dtest-upgrade .

# Custom unittest and doctest runners

The normal command-line `unittest` and `doctest` runners do not
distinguish between comparison failures and exceptions when reporting
their exit status. We provide custom runners to workaround this.

For `unittest`, replace:

    $ python -m unittest script

with:

    $ dtest-unittest script

For `doctest`, replace:

    $ python -m doctest script.py

with:

    $ dtest-doctest script.py
