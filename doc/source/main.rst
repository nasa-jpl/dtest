.. index:: JPL Darts/Dshell testing framework (the Dtest module)

.. _Dtest_Main:

=====================
Dtest Module Overview
=====================

.. contents::
   :depth: 3


Introduction
============

The Dtest module contains an automated software validation framework, featuring extensive support
for regression testing of C/C++ and Python code.  This module contains several useful program
verification utilities including:

  * `dtest` - Runs sets of regression tests
  * `compareCheckpointFiles` - Compares checkpoint output files
  * `compareModelFiles` - Compares model definition files
  * `compareDictsInFiles` - Compares Python dictionaries embedded in text files
  * `Ddoctest` - a drop-in replacement for the python 'doctest' library that
    does numerical comparisons with relative and absolute tolerances.


.. toctree::
   :maxdepth: 3

   testing.rst
   usage.rst
   dunit.rst
