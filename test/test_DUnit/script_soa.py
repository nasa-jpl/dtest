from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from sys import float_info

from Dtest.dunit import DUnitTest
from Dtest.dunit import DUnitTestRunner
from Dtest.dunit.DUnitFactorySoa import FactorySoa
from Dtest.dunit.DUnitTest import RequirementIdentifier as Req

from Math.SOA_Py import SOAQuaternion
from Math.SOA_Py import SOAMatrix33
from Math.SOA_Py import SOAMatrix44
from Math.SOA_Py import SOAVector3
from Math.SOA_Py import SOAVector4


class vDUnit(DUnitTest.DUnit):
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
        Integer, Real, SOAMatrix33, SOAQuaternion, SOAVector3, String
    """

    def test_evalEqual(self):
        # TODO: Need to create tests for SOAVector4
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

        # SOAMatrix33
        expectedValue = SOAMatrix33([[1.1, 2.2, 3.3], [4.4, 5.5, 6.6], [7.7, 8.8, 9.9]])
        actualValue = SOAMatrix33([[1.1, 2.2, 3.3], [4.4, 5.5, 6.6], [7.7, 8.8, 9.9]])
        self.evalExpTrue(
            Req("evalEqual-SOAMatrix33-01"),
            self.evalEqual(Req(""), expectedValue, actualValue, None, None),
        )

        expectedValue = SOAMatrix33([[1.1, 2.2, 3.3], [4.4, 5.5, 6.6], [7.7, 8.8, 9.9]])
        actualValue = SOAMatrix33([[1.1, 1.1, 1.1], [1.1, 1.1, 1.1], [1.1, 1.1, 1.1]])
        self.evalExpFalse(
            Req("evalEqual-SOAMatrix33-02"),
            self.evalEqual(Req(""), expectedValue, actualValue, None, None),
        )

        # SOAMatrix44
        expectedValue = SOAMatrix44(
            [
                [1.1, 2.2, 3.3, 4.4],
                [2.2, 3.3, 4.4, 5.5],
                [3.3, 4.4, 5.5, 6.6],
                [4.4, 5.5, 6.6, 7.7],
            ]
        )
        actualValue = SOAMatrix44(
            [
                [1.1, 2.2, 3.3, 4.4],
                [2.2, 3.3, 4.4, 5.5],
                [3.3, 4.4, 5.5, 6.6],
                [4.4, 5.5, 6.6, 7.7],
            ]
        )
        self.evalExpTrue(
            Req("evalEqual-SOAMatrix44-01"),
            self.evalEqual(Req(""), expectedValue, actualValue, None, None),
        )

        expectedValue = SOAMatrix44(
            [
                [1.1, 2.2, 3.3, 4.4],
                [2.2, 3.3, 4.4, 5.5],
                [3.3, 4.4, 5.5, 6.6],
                [4.4, 5.5, 6.6, 7.7],
            ]
        )
        actualValue = SOAMatrix44(
            [
                [1.1, 2.2, 3.3, 4.4],
                [2.2, 3.3, 4.4, 5.5],
                [3.3, 4.4, 5.5, 6.6],
                [4.4, 5.5, 6.6, 7.0],
            ]
        )
        self.evalExpFalse(
            Req("evalEqual-SOAMatrix44-02"),
            self.evalEqual(Req(""), expectedValue, actualValue, None, None),
        )

        # SOAQuaternion
        expectedValue = FactorySoa.newQuaternion(1.1, 2.2, 3.3, 4.4)
        actualValue = FactorySoa.newQuaternion(1.1, 2.2, 3.3, 4.4)
        self.evalExpTrue(
            Req("evalEqual-SOAQuaternion-01"),
            self.evalEqual(Req(""), expectedValue(), actualValue(), None, None),
        )

        expectedValue = SOAVector4(1.1, 2.2, 3.3, 4.4)
        expectedValue.normalize()
        expectedValue = SOAQuaternion(expectedValue)
        actualValue = SOAVector4(1.1, 1.1, 1.1, 1.1)
        actualValue.normalize()
        actualValue = SOAQuaternion(actualValue)
        self.evalExpFalse(
            Req("evalEqual-SOAQuaternion-02"),
            self.evalEqual(Req(""), expectedValue(), actualValue(), None, None),
        )

        # SOAVector3
        expectedValue = SOAVector3(1.1, 2.2, 3.3)
        actualValue = SOAVector3(1.1, 2.2, 3.3)
        self.evalExpTrue(
            Req("evalEqual-SOAVector3-01"),
            self.evalEqual(Req(""), expectedValue(), actualValue(), None, None),
        )

        expectedValue = SOAVector3(1.1, 2.2, 3.3)
        actualValue = SOAVector3(1.1, 1.1, 1.1)
        self.evalExpFalse(
            Req("evalEqual-SOAVector3-02"),
            self.evalEqual(Req(""), expectedValue(), actualValue(), None, None),
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

        # Real
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

        # SOAMatrix33
        expectedValue = [
            SOAMatrix33([[1.1, 2.2, 3.3], [4.4, 5.5, 6.6], [7.7, 8.8, 9.9]]),
            SOAMatrix33([[1.1, 2.2, 3.3], [4.4, 5.5, 6.6], [7.7, 8.8, 9.9]]),
        ]
        actualValue = [
            SOAMatrix33([[1.1, 2.2, 3.3], [4.4, 5.5, 6.6], [7.7, 8.8, 9.9]]),
            SOAMatrix33([[1.1, 2.2, 3.3], [4.4, 5.5, 6.6], [7.7, 8.8, 9.9]]),
        ]
        self.evalExpTrue(
            Req("evalListEqual-SOAMatrix33-01"),
            self.evalEqual(Req(""), expectedValue, actualValue, None, False),
        )

        expectedValue = [
            SOAMatrix33([[1.1, 2.2, 3.3], [4.4, 5.5, 6.6], [7.7, 8.8, 9.9]]),
            SOAMatrix33([[1.1, 2.2, 3.3], [4.4, 5.5, 6.6], [7.7, 8.8, 9.9]]),
        ]
        actualValue = [
            SOAMatrix33([[1.1, 1.1, 1.1], [1.1, 1.1, 1.1], [1.1, 1.1, 1.1]]),
            SOAMatrix33([[1.1, 1.1, 1.1], [1.1, 1.1, 1.1], [1.1, 1.1, 1.1]]),
        ]
        self.evalExpFalse(
            Req("evalListEqual-SOAMatrix33-02"),
            self.evalEqual(Req(""), expectedValue, actualValue, None, False),
        )

        # SOAQuaternion
        e1 = SOAVector4(1.1, 2.2, 3.3, 4.4)
        e2 = SOAVector4(1.1, 2.2, 3.3, 4.4)
        e1.normalize()
        e2.normalize()
        expectedValue = [SOAQuaternion(e1), SOAQuaternion(e2)]
        a1 = SOAVector4(1.1, 2.2, 3.3, 4.4)
        a2 = SOAVector4(1.1, 2.2, 3.3, 4.4)
        a1.normalize()
        a2.normalize()
        actualValue = [SOAQuaternion(a1), SOAQuaternion(a2)]
        self.evalExpTrue(
            Req("evalListEqual-SOAQuaternion-01"),
            self.evalEqual(Req(""), expectedValue, actualValue, None, False),
        )

        e1 = SOAVector4(1.1, 2.2, 3.3, 4.4)
        e2 = SOAVector4(1.1, 2.2, 3.3, 4.4)
        e1.normalize()
        e2.normalize()
        expectedValue = [SOAQuaternion(e1)(), SOAQuaternion(e2)()]
        a1 = SOAVector4(1.1, 1.1, 1.1, 1.1)
        a2 = SOAVector4(1.1, 1.1, 1.1, 1.1)
        a1.normalize()
        a2.normalize()
        actualValue = [SOAQuaternion(a1)(), SOAQuaternion(a2)()]
        self.evalExpFalse(
            Req("evalListEqual-SOAQuaternion-02"),
            self.evalEqual(Req(""), expectedValue, actualValue, None, False),
        )

        # SOAVector3
        expectedValue = [SOAVector3(1.1, 2.2, 3.3), SOAVector3(1.1, 2.2, 3.3)]
        actualValue = [SOAVector3(1.1, 2.2, 3.3), SOAVector3(1.1, 2.2, 3.3)]
        self.evalExpTrue(
            Req("evalListEqual-SOAVector3-01"),
            self.evalEqual(Req(""), expectedValue, actualValue, None, False),
        )

        expectedValue = [
            SOAVector3(1.1, 2.2, 3.3)(),
            SOAVector3(1.1, 2.2, 3.3)(),
        ]
        actualValue = [SOAVector3(1.1, 1.1, 1.1)(), SOAVector3(1.1, 1.1, 1.1)()]
        self.evalExpFalse(
            Req("evalListEqual-SOAVector3-02"),
            self.evalEqual(Req(""), expectedValue, actualValue, None, False),
        )

        # String
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

        # SOAMatrix33
        expectedValue = SOAMatrix33([[1.1, 2.2, 3.3], [4.4, 5.5, 6.6], [7.7, 8.8, 9.9]])
        actualValue = SOAMatrix33(
            [
                [1.1, 2.2, 3.3],
                [4.4, 5.5, 6.6],
                [7.7, 8.8, 9.9 + float_info.epsilon],
            ]
        )
        self.evalExpTrue(
            Req("evalEqualDelta-SOAMatrix33-01"),
            self.evalEqualDelta(Req(""), expectedValue, actualValue, delta, None, False),
        )

        expectedValue = SOAMatrix33([[1.1, 2.2, 3.3], [4.4, 5.5, 6.6], [7.7, 8.8, 9.9]])
        actualValue = SOAMatrix33([[1.1, 1.1, 1.1], [1.1, 1.1, 1.1], [1.1, 1.1, 1.1]])
        self.evalExpFalse(
            Req("evalEqualDelta-SOAMatrix33-02"),
            self.evalEqualDelta(Req(""), expectedValue, actualValue, delta, None, False),
        )

        # SOAQuaternion
        expectedValue = SOAVector4(1.1, 2.2, 3.3, 4.4)
        expectedValue.normalize()
        expectedValue = SOAQuaternion(expectedValue)
        actualValue = SOAVector4(1.1, 2.2, 3.3, 4.4 + float_info.epsilon)
        actualValue.normalize()
        actualValue = SOAQuaternion(actualValue)
        self.evalExpTrue(
            Req("evalEqualDelta-SOAQuaternion-01"),
            self.evalEqualDelta(Req(""), expectedValue, actualValue, delta, None, False),
        )

        expectedValue = SOAVector4(1.1, 2.2, 3.3, 4.4)
        expectedValue.normalize()
        expectedValue = SOAQuaternion(expectedValue)
        actualValue = SOAVector4(1.1, 1.1, 1.1, 1.1)
        actualValue.normalize()
        actualValue = SOAQuaternion(actualValue)
        self.evalExpFalse(
            Req("evalEqualDelta-SOAQuaternion-02"),
            self.evalEqualDelta(Req(""), expectedValue, actualValue, delta, None, False),
        )

        # SOAVector3
        expectedValue = SOAVector3(1.1, 2.2, 3.3)
        actualValue = SOAVector3(1.1, 2.2, 3.3 + float_info.epsilon)
        self.evalExpTrue(
            Req("evalEqualDelta-SOAVector3-01"),
            self.evalEqualDelta(Req(""), expectedValue(), actualValue(), delta, None, False),
        )

        expectedValue = SOAVector3(1.1, 2.2, 3.3)
        actualValue = SOAVector3(1.1, 1.1, 1.1)
        self.evalExpFalse(
            Req("evalEqualDelta-SOAVector3-02"),
            self.evalEqualDelta(Req(""), expectedValue(), actualValue(), delta, None, False),
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

        # SOAMatrix33
        expectedValue = SOAMatrix33([[1.1, 2.2, 3.3], [4.4, 5.5, 6.6], [7.7, 8.8, 9.9]])
        actualValue = SOAMatrix33([[1.1, 2.2, 3.3], [4.4, 5.5, 6.6], [7.7, 8.8, 9.9 + 0.00001]])
        self.evalExpTrue(
            Req("evalEqualVariance-SOAMatrix33-01"),
            self.evalEqualVariance(Req(""), expectedValue, actualValue, deltaVariance, None, False),
        )

        expectedValue = SOAMatrix33([[1.1, 2.2, 3.3], [4.4, 5.5, 6.6], [7.7, 8.8, 9.9]])
        actualValue = SOAMatrix33([[1.1, 1.1, 1.1], [1.1, 1.1, 1.1], [1.1, 1.1, 1.1]])
        self.evalExpFalse(
            Req("evalEqualVariance-SOAMatrix33-02"),
            self.evalEqualVariance(Req(""), expectedValue, actualValue, deltaVariance, None, False),
        )

        # SOAQuaternion
        expectedValue = SOAVector4(1.1, 2.2, 3.3, 4.4)
        expectedValue.normalize()
        expectedValue = SOAQuaternion(expectedValue)
        actualValue = SOAVector4(1.1, 2.2, 3.3, 4.4 + 0.00001)
        actualValue.normalize()
        actualValue = SOAQuaternion(actualValue)
        self.evalExpTrue(
            Req("evalEqualVariance-SOAQuaternion-01"),
            self.evalEqualVariance(Req(""), expectedValue, actualValue, deltaVariance, None, False),
        )

        expectedValue = SOAVector4(1.1, 2.2, 3.3, 4.4)
        expectedValue.normalize()
        expectedValue = SOAQuaternion(expectedValue)
        actualValue = SOAVector4(1.1, 1.1, 1.1, 1.1)
        actualValue.normalize()
        actualValue = SOAQuaternion(actualValue)
        self.evalExpFalse(
            Req("evalEqualVariance-SOAQuaternion-02"),
            self.evalEqualVariance(Req(""), expectedValue, actualValue, deltaVariance, None, False),
        )

        # SOAVector3
        expectedValue = SOAVector3(1.1, 2.2, 3.3)
        actualValue = SOAVector3(1.1, 2.2, 3.3 + 0.00001)
        self.evalExpTrue(
            Req("evalEqualVariance-SOAVector3-01"),
            self.evalEqualVariance(
                Req(""),
                expectedValue(),
                actualValue(),
                deltaVariance,
                None,
                False,
            ),
        )

        expectedValue = SOAVector3(1.1, 2.2, 3.3)
        actualValue = SOAVector3(1.1, 1.1, 1.1)
        self.evalExpFalse(
            Req("evalEqualVariance-SOAVector3-02"),
            self.evalEqualVariance(
                Req(""),
                expectedValue(),
                actualValue(),
                deltaVariance,
                None,
                False,
            ),
        )


if __name__ == "__main__":
    DUnitTestRunner.DUnitRunner(evalStdOut=True, evalStdOutOnlyFail=True)
