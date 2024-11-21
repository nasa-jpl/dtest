=============
DUnitUnittest
=============
Class Documentation
-------------------

.. contents::
   :depth: 2

Introduction
============

DUnitUnit extends and uses the native python unittest framework. DUnitUnit is a specialized unit tester
facilitating the collection of evaluation results and its requirement identifier at the evaluation statement
rather than the method.


Example Usage Syntax
====================

.. code-block:: python

  from Dtest.dunit import DUnitUnittest
  from Dtest.dunit import DUnitTestRunner
  from Dtest.dunit.DUnitUnittest import RequirementIdentifier as Req

  class vDUnitUnit(DUnitUnittest.CompassUnit):
    def test_evalEqual(self):
      expectedValue = 1
      actualValue = 1
      self.evalEqual(Req("evalEqual-Integer-01"), expectedValue, actualValue)

  if __name__ == '__main__':
    DUnitTestRunner.DUnitRunner(evalStdOut=True, evalStdOutOnlyFail=True)


TODO: Additional comments concerning the code example.


Related Regression Tests
========================

.. toctree::
  :maxdepth: 1

TODO: Insert link to vDUnitUnittest.rst file.


DUnitUnittest Class API Documentation
=====================================

.. note::

   .. automodule:: Dtest.dunit.DUnitTest
