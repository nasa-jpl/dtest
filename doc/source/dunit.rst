.. _Dtest_DUnit:

.. index:: DUnit Testing Framework

DUnit Testing Framework
=======================

Introduction
------------
DUnit extends and uses the native python unittest framework. DUnit is a specialized
unit tester facilitating the collection of evaluation results and its requirement identifier at
the evaluation statement rather than the method.

DUnit add the following capabilities:
 * Comparisons between lists, with or without a tolerance
 * Comparisons between SOA Vectors, Matrices, Eulers, and Quaternions
 * Comparisons between rotations, recognizing equivalent but not-identical values
 * Comparisons using variance, to measure relative difference as opposed to absolute difference
 * Comparisons that convey metadata for the purposes of process / metrics


Extends Python Unittest
-----------------------
DUnit is an extension of Python Unittest. Therefore, it has the same file structure and basic
behavior as Unittest, with a few exceptions. Most importantly, the previous assertion methods
have been deprecated, and replaced with our own assertion methods. You may, however, use the
setup and teardown methods as you would in Unittest.


DUnit Output
------------
DUnit provides custom formatted output results for each individual assertion you make to both
ASCII and XML formats. This output must be turned on if desired though, as it is suppressed by
default. To turn on the file output, set the environment variable DUNIT_FILE_OUT to 'True'.

DUnit also provides output to standard out, if desired. The following arguments control that output:
  * evalStdOut
    - True sends results to standard out. False sends no results to standard out.
  * evalStdOutOnlyFail
    - True sends only FAIL results to standard out. False sends all results to standard out.


Example Usage Syntax
--------------------
.. code-block:: python

  from Dtest.dunit import DUnitTest
  from Dtest.dunit import DUnitTestRunner
  from Dtest.dunit.DUnitTest import RequirementIdentifier as Req

  class CovarianceDispersionTest(DUnitTest.DUnit):
    def test_evaluations(self):
      expectedValue = 1
      actualValue = 1
      self.evalEqual(Req("REQ-001"), expectedValue, actualValue)
      self.evalEqualDelta(Req("REQ-001"), expectedValue, actualValue, 1e-10)
      self.evalExpTrue(Req("REQ-001"), expectedValue > actualValue)

  if __name__ == '__main__':
    DUnitTestRunner.DUnitRunner(evalStdOut=True, evalStdOutOnlyFail=True)

The above code shows a basic DUnit test. After importing the necessary libraries, the tester
makes his test a subclass of DUnit. The test method shows 3 of the common evaluation types:

 * evalEqual will compare the value 1 to 1, and evaluate as PASS.
 * evalEqualDelta will compare the same numbers within a tolerance of 1e-10, also evaluating to PASS.
 * evalExpTrue will test the expression '1 >1', which will evaluate to FAIL.

The final line shows the arguments used for output, turning on standard output, but only for
tests that FAIL.


DUnit Methods
-------------

.. toctree::
   :maxdepth: 1

   dunit/DUnitFactoryEvaluation.rst
   dunit/DUnitFactoryResult.rst
   dunit/DUnitFactorySoa.rst
   dunit/DUnitTestRunner.rst
   dunit/DUnitTest.rst
