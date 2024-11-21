"""
Unit test for basic DUnit data types of Integer, Real, and String.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from sys import float_info

from Dtest.dunit import DUnitTest
from Dtest.dunit import DUnitTestRunner
from Dtest.dunit.DUnitTest import RequirementIdentifier as Req


class BasicDUnit(DUnitTest.DUnit):
    """
    Numbers:
        Common:
            Zero:    -0, 0, +0

        Integer:
            Maximum: maxint, +maxint
            Minimum: -maxint-1

        Real:
            Epsilon:  -sys.float_info.epsilon, sys.float_info.epsilon, +sys.float_info.epsilon
            Infinity: "-inf", "inf", "+inf"
            Maximum:  -sys.float_info.max, sys.float_info.max, +sys.float_info.max
            Minimum:  -sys.float_info.min, sys.float_info.min, +sys.float_info.min
            Nan:      "-nan", "nan", "+nan"

    Test Types:
        Integer, Real, String
    """

    def test_evalEqual(self):
        # Integer
        expectedValue = 1
        actualValue = 1
        self.evalExpTrue(
            Req("evalEqual-Integer-01"),
            self.evalEqual(Req(""), expectedValue, actualValue, None, None),
        )

        expectedValue = 1
        actualValue = 2
        self.evalExpFalse(
            Req("evalEqual-Integer-02"),
            self.evalEqual(Req(""), expectedValue, actualValue, None, None),
        )

        # Real
        expectedValue = 1.23456e-4
        actualValue = 1.23456e-4
        self.evalExpTrue(
            Req("evalEqual-Real-01"),
            self.evalEqual(Req(""), expectedValue, actualValue, None, None),
        )

        expectedValue = 1.23456e-4
        actualValue = 1.23456
        self.evalExpFalse(
            Req("evalEqual-Real-02"),
            self.evalEqual(Req(""), expectedValue, actualValue, None, None),
        )

        # String
        expectedValue = "Success"
        actualValue = "Success"
        self.evalExpTrue(
            Req("evalEqual-String-01"),
            self.evalEqual(Req(""), expectedValue, actualValue, None, None),
        )

        expectedValue = "Success"
        actualValue = "Failure"
        self.evalExpFalse(
            Req("evalEqual-String-02"),
            self.evalEqual(Req(""), expectedValue, actualValue, None, None),
        )

    def test_evalEqualList(self):
        # Integer
        expectedValue = [1, 2, 3]
        actualValue = [1, 2, 3]
        self.evalExpTrue(
            Req("evalListEqual-Integer-01"),
            self.evalEqual(Req(""), expectedValue, actualValue, None, False),
        )

        expectedValue = [1, 2, 3]
        actualValue = [1, 2, 2]
        self.evalExpFalse(
            Req("evalListEqual-Integer-02"),
            self.evalEqual(Req(""), expectedValue, actualValue, None, False),
        )

        # Comment: Real
        expectedValue = [1.23456e-4, 1.23456e-5, 1.23456e-6]
        actualValue = [1.23456e-4, 1.23456e-5, 1.23456e-6]
        self.evalExpTrue(
            Req("evalListEqual-Real-01"),
            self.evalEqual(Req(""), expectedValue, actualValue, None, False),
        )

        expectedValue = [1.23456e-4, 1.23456e-5, 1.23456e-6]
        actualValue = [1.23456, 1.23456e-5, 1.23456e-6]
        self.evalExpFalse(
            Req("evalListEqual-Real-02"),
            self.evalEqual(Req(""), expectedValue, actualValue, None, False),
        )

        # Comment: String
        expectedValue = ["Success", "Success", "Success"]
        actualValue = ["Success", "Success", "Success"]
        self.evalExpTrue(
            Req("evalListEqual-String-01"),
            self.evalEqual(Req(""), expectedValue, actualValue, None, False),
        )

        expectedValue = ["Success", "Success", "Success"]
        actualValue = ["Success", "Failure", "Success"]
        self.evalExpFalse(
            Req("evalListEqual-String-02"),
            self.evalEqual(Req(""), expectedValue, actualValue, None, False),
        )

    def test_evalEqualDelta(self):
        # Integer
        delta = 1

        expectedValue = 1
        actualValue = 2
        self.evalExpTrue(
            Req("evalEqualDelta-Integer-01"),
            self.evalEqualDelta(Req(""), expectedValue, actualValue, delta, None, False),
        )

        expectedValue = 1
        actualValue = 2 + 1
        self.evalExpFalse(
            Req("evalEqualDelta-Integer-02"),
            self.evalEqualDelta(Req(""), expectedValue, actualValue, delta, None, False),
        )

        # Real
        delta = float_info.epsilon

        #        # FAIL
        #        delta = 0.001
        #        expectedValue = 1.23456e-4
        #        actualValue = 1.23456e-4 + 0.00001

        #        # PASS
        #        delta = 0.00001
        #        expectedValue = 1.23456e-4
        #        actualValue = 1.23456e-4 + delta

        #        # PASS
        #        delta = float_info.epsilon
        #        expectedValue = 1.23456e-4
        #        actualValue = 1.23456e-4 + delta

        # TODO: Need to determine what to do to handle this situation.
        #        # FAIL
        #        delta = float_info.epsilon * 1.0e-4
        #        expectedValue = 1.23456e-20
        #        actualValue = 1.23456e-20 + delta

        #        # PASS
        #        delta = 1.0e-20
        #        expectedValue = 1.0e-20
        #        actualValue = 1.0e-20 + delta

        #        print "expectedValue: %1.200f" %expectedValue
        #        print "actualValue:   %1.200f" %actualValue
        #        print "delta:         %1.200f" %delta
        #        print "difference:    %1.200f" %(actualValue - expectedValue)

        expectedValue = 1.23456e-4
        actualValue = 1.23456e-4 + delta
        self.evalExpTrue(
            Req("evalEqualDelta-Real-01"),
            self.evalEqualDelta(Req(""), expectedValue, actualValue, delta, None, False),
        )

        expectedValue = 1.23456e-4
        actualValue = 1.23456
        self.evalExpFalse(
            Req("evalEqualDelta-Real-02"),
            self.evalEqualDelta(Req(""), expectedValue, actualValue, delta, None, False),
        )

    def test_evalEqualVariance(self):
        # Integer
        deltaVariance = 1.0

        expectedValue = 1
        actualValue = 2
        self.evalExpTrue(
            Req("evalEqualVariance-Integer-01"),
            self.evalEqualVariance(Req(""), expectedValue, actualValue, deltaVariance, None, False),
        )
        self.evalEqualVariance(Req(""), expectedValue, actualValue, deltaVariance)

        expectedValue = 1
        actualValue = 2 + 1
        self.evalExpFalse(
            Req("evalEqualVariance-Integer-02"),
            self.evalEqualVariance(Req(""), expectedValue, actualValue, deltaVariance, None, False),
        )

        # Real
        deltaVariance = 0.00001

        expectedValue = 1.23456e-4
        actualValue = 1.23456e-4 + 1.0e-9
        self.evalExpTrue(
            Req("evalEqualVariance-Real-01"),
            self.evalEqualVariance(Req(""), expectedValue, actualValue, deltaVariance, None, False),
        )
        self.evalEqualVariance(Req(""), expectedValue, actualValue, deltaVariance)

        expectedValue = 1.23456e-4
        actualValue = 1.23456
        self.evalExpFalse(
            Req("evalEqualVariance-Real-02"),
            self.evalEqualVariance(Req(""), expectedValue, actualValue, deltaVariance, None, False),
        )


if __name__ == "__main__":
    DUnitTestRunner.DUnitRunner(evalStdOut=True, evalStdOutOnlyFail=True)
