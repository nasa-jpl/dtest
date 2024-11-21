"""
FactoryEvaluation is a factory-based object used to create EvaluationObj
objects.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from math import fabs

# Add try/except logic to allow importing without SOA.  This basically
# allows use with non-Dshell based packages, thus not having to include
# another 10 modules just to have Dtest capability.
try:
    from Math.SOA_Py import SOAMatrix
    from Math.SOA_Py import SOAMatrix33
    from Math.SOA_Py import SOAMatrix44
    from Math.SOA_Py import SOAQuaternion
    from Math.SOA_Py import SOAVector
    from Math.SOA_Py import SOAVector3
    from Math.SOA_Py import SOAVector4
except ImportError:

    class SOANoneType(object):
        pass

    SOAMatrix = SOANoneType
    SOAMatrix33 = SOANoneType
    SOAMatrix44 = SOANoneType
    SOAQuaternion = SOANoneType
    SOAVector = SOANoneType
    SOAVector3 = SOANoneType
    SOAVector4 = SOANoneType
    import warnings

    warnings.warn("Unable to import from Math.SOA_Py--> " + "Continuing without SOA functionality.")

# Add try/except logic to allow using MathConstants.BIG
# without having the DshellEnv module.
try:
    import Math.MathConstants_Py as MathConstants
except:

    class MathConstants(object):
        BIG = 1e20


class FactoryEvaluation:
    """
    | FactoryEvaluation is a factory-based object used to create
    | EvaluationObj objects.
    """

    @staticmethod
    def newEvaluationObj(
        expected_value,
        actual_value,
        delta=None,
        delta_variance=None,
        rotation=False,
    ):
        """
        | Factory method that creates a EvaluationObj object from values.
        """
        if rotation is True:
            if isinstance(expected_value, SOAQuaternion):
                if isinstance(actual_value, SOAQuaternion):
                    return EvaluationQuaternionRotation(expected_value, actual_value, delta, delta_variance)

        if isinstance(expected_value, SOAMatrix):
            if isinstance(actual_value, SOAMatrix):
                return EvaluationMatrix(expected_value, actual_value, delta, delta_variance)

        if isinstance(expected_value, SOAMatrix33):
            if isinstance(actual_value, SOAMatrix33):
                return EvaluationMatrix(expected_value, actual_value, delta, delta_variance)

        if isinstance(expected_value, SOAMatrix44):
            if isinstance(actual_value, SOAMatrix44):
                return EvaluationMatrix(expected_value, actual_value, delta, delta_variance)

        if isinstance(expected_value, SOAQuaternion):
            if isinstance(actual_value, SOAQuaternion):
                return EvaluationQuaternion(expected_value, actual_value, delta, delta_variance)

        if isinstance(expected_value, SOAVector):
            if isinstance(actual_value, SOAVector):
                return EvaluationVector(expected_value, actual_value, delta, delta_variance)

        if isinstance(expected_value, SOAVector3):
            if isinstance(actual_value, SOAVector3):
                return EvaluationVector(expected_value, actual_value, delta, delta_variance)

        if isinstance(expected_value, bool):
            return EvaluationAlphanumeric(expected_value, actual_value, delta, delta_variance)

        if isinstance(expected_value, int):
            return EvaluationAlphanumeric(expected_value, actual_value, delta, delta_variance)

        if isinstance(expected_value, float):
            return EvaluationAlphanumeric(expected_value, actual_value, delta, delta_variance)

        if isinstance(expected_value, str):
            if isinstance(actual_value, str):
                return EvaluationAlphanumeric(expected_value, actual_value, delta, delta_variance)

        return None


class EvaluationObj:
    """
    | Base object containing common information usable by derived classes.
    """

    def __init__(self, expected_value, actual_value, delta, delta_variance):
        self._expected_value = expected_value
        self._actual_value = actual_value
        self._delta = delta
        self._delta_variance = delta_variance

    @staticmethod
    def _differenceSimple(expected_value, actual_value):
        return actual_value - expected_value

    @staticmethod
    def _differenceSOAQuaternion(expected_value, actual_value):
        return actual_value.vec4() - expected_value.vec4()

    def _evalEqual(self):
        pass

    def _evalDelta(self):
        pass

    def _evalVariance(self):
        pass

    @staticmethod
    def getDifference(expected_value, actual_value):
        """
        | Calculates the difference of two objects as determined by the
        | object type.
        | Supports float, int, Math.SOA_Py.SOAVector, and
        | Math.SOA_Py.SOAQuaternion object types.
        |
        | Returns the difference.
        """
        if (
            isinstance(expected_value, float)
            or isinstance(expected_value, int)
            or isinstance(expected_value, SOAVector)
            or isinstance(expected_value, SOAVector3)
            or isinstance(expected_value, SOAVector4)
        ):
            return EvaluationObj._differenceSimple(expected_value, actual_value)

        if isinstance(expected_value, SOAQuaternion):
            return EvaluationObj._differenceSOAQuaternion(expected_value, actual_value)

    @staticmethod
    def getVariance(expected_value, actual_value):
        """
        | Calculates the variance of two objects as determined by the
        | object type.
        | Supports float, int, Math.SOA_Py.SOAVector, and
        | Math.SOA_Py.SOAQuaternion object types.
        |
        | Returns the variance.
        """
        # Equation: ( ( (Actual - Expected) / (Expected) ) * 100)
        # = actual variance
        if isinstance(expected_value, float) or isinstance(expected_value, int):
            if expected_value == 0:
                if actual_value == 0:
                    return 0.0
                else:
                    return MathConstants.BIG
            else:
                diff = EvaluationObj.getDifference(expected_value, actual_value)
                return diff / expected_value

        if isinstance(expected_value, SOAQuaternion):
            if expected_value.vec4().magnitude() == 0.0:
                if actual_value.vec4().magnitude() == 0.0:
                    return 0.0
                else:
                    return MathConstants.BIG
            else:
                diff = EvaluationObj.getDifference(expected_value, actual_value).magnitude()
                return diff / expected_value.vec4().magnitude()

        if isinstance(expected_value, SOAVector):
            if expected_value.magnitude() == 0.0:
                if actual_value.magnitude() == 0.0:
                    return 0.0
                else:
                    return MathConstants.BIG
            else:
                diff = EvaluationObj.getDifference(expected_value, actual_value).magnitude()
                return diff / expected_value.magnitude()

    @staticmethod
    def isEqual(expected_value, actual_value):
        """
        | Compares the expected_value to the actual_value and determines
        | if they are equal.
        |
        | Returns True if the values are equal, else returns False.
        """
        return bool(actual_value == expected_value)

    @staticmethod
    def fixQuaternion(soa_quaternion):
        """
        | Fixes the Math.SOA_Py.SOAQuaternion object; specifically inverses
        | the sign of each element if the fourth element is less than zero.
        |
        | Returns the "fixed" Math.SOA_Py.SOAQuaternion object.
        """
        soa_quaternion.normalize()
        q0 = soa_quaternion.q0()
        if q0 < 0:
            return SOAQuaternion(
                -soa_quaternion[0],
                -soa_quaternion[1],
                -soa_quaternion[2],
                -q0,
            )
        else:
            return soa_quaternion

    @staticmethod
    def verifySizeOfMatricesAreEqual(expected_matrix, actual_matrix):
        """
        | Compares the size of the expected_matrix to the size of the
        | actual_matrix.
        |
        | Returns True if the sizes are equal, else returns False.
        """
        if expected_matrix.cols() == actual_matrix.cols():
            if expected_matrix.rows() == actual_matrix.rows():
                return True
        return False

    def performEvaluation(self):
        """
        | Virtual method.
        | Executes the evaluation comparison logic as specified by delta
        | and variance values as applicable.
        |
        | Returns the boolean result of the evaluation.
        """
        if self._delta is None and self._delta_variance is None:
            return self._evalEqual()

        if self._delta is not None and self._delta_variance is None:
            return self._evalDelta()

        if self._delta is None and self._delta_variance is not None:
            return self._evalVariance()

        return False


class EvaluationAlphanumeric(EvaluationObj):
    """
    | Derived object for handling alphanumeric evaluations.
    """

    def __init__(self, expected_value, actual_value, delta, delta_variance):
        EvaluationObj.__init__(self, expected_value, actual_value, delta, delta_variance)

    def _evalEqual(self):
        return bool(self.isEqual(self._expected_value, self._actual_value))

    def _evalDelta(self):
        return fabs(self.getDifference(self._expected_value, self._actual_value)) <= self._delta

    def _evalVariance(self):
        return fabs(self.getVariance(self._expected_value, self._actual_value)) <= self._delta_variance


class EvaluationMatrix(EvaluationObj):
    """
    | Derived object for handling Math.SOA_Py.SOAMatrix evaluations.
    """

    def __init__(self, expected_matrix, actual_matrix, delta, delta_variance):
        EvaluationObj.__init__(self, expected_matrix, actual_matrix, delta, delta_variance)

    def _evalEqual(self):
        for row in range(self._expected_value.rows()):
            for col in range(self._expected_value.cols()):
                if not self.isEqual(
                    self._expected_value[row, col],
                    self._actual_value[row, col],
                    # self._expected_value.getElement(row, col),
                    # self._actual_value.getElement(row, col),
                ):
                    return False
        return True

    def _evalDelta(self):
        for row in range(self._expected_value.rows()):
            for col in range(self._expected_value.cols()):
                ev = self._expected_value[row, col]
                av = self._actual_value[row, col]
                if not (fabs(self.getDifference(ev, av)) <= self._delta):
                    return False
        return True

    def _evalVariance(self):
        for row in range(self._expected_value.rows()):
            for col in range(self._expected_value.cols()):
                ev = self._expected_value[row, col]
                av = self._actual_value[row, col]
                if not (fabs(self.getVariance(ev, av)) <= self._delta_variance):
                    return False
        return True

    def performEvaluation(self):
        """
        | Overridden virtual method.
        | Verifies the Math.SOA_Py.SOAMatrix objects are the same size and
        | then executes the base object performEvaluation() method.
        |
        | Returns the boolean result of the evaluation if objects sizes are
        | equal, else returns False.
        """
        if self.verifySizeOfMatricesAreEqual(self._expected_value, self._actual_value) is False:
            return False

        return EvaluationObj.performEvaluation(self)


class EvaluationQuaternion(EvaluationObj):
    """
    | Derived object for handling Math.SOA_Py.SOAQuaternion evaluations.
    """

    def __init__(self, expected_quaternion, actual_quaternion, delta, delta_variance):
        expected_quaternion = self.fixQuaternion(expected_quaternion)
        actual_quaternion = self.fixQuaternion(actual_quaternion)
        EvaluationObj.__init__(self, expected_quaternion, actual_quaternion, delta, delta_variance)

    def _evalEqual(self):
        return bool(self.getDifference(self._expected_value.vec4(), self._actual_value.vec4()).magnitude() == 0)

    def _evalDelta(self):
        return fabs(self.getDifference(self._expected_value, self._actual_value).magnitude()) <= self._delta

    def _evalVariance(self):
        return fabs(self.getVariance(self._expected_value, self._actual_value)) <= self._delta_variance


class EvaluationQuaternionRotation(EvaluationObj):
    """
    | Derived object for handling rotational Math.SOA_Py.SOAQuaternion
    | evaluations.
    """

    def __init__(self, expected_quaternion, actual_quaternion, delta, delta_variance):
        expected_quaternion = self.fixQuaternion(expected_quaternion)
        actual_quaternion = self.fixQuaternion(actual_quaternion)

        EvaluationObj.__init__(self, expected_quaternion, actual_quaternion, delta, delta_variance)

    def _rotationCompare(self):
        unitx = SOAVector3([1, 0, 0])
        unity = SOAVector3([0, 1, 0])
        unitz = SOAVector3([0, 0, 1])

        ev = self._expected_value
        av = self._actual_value
        f1 = FactoryEvaluation.newEvaluationObj((ev * unitx), (av * unitx), self._delta, self._delta_variance)
        f2 = FactoryEvaluation.newEvaluationObj((ev * unity), (av * unity), self._delta, self._delta_variance)
        f3 = FactoryEvaluation.newEvaluationObj((ev * unitz), (av * unitz), self._delta, self._delta_variance)

        if f1 is not None and f2 is not None and f3 is not None:
            return f1.performEvaluation() and f2.performEvaluation() and f3.performEvaluation()

    def _evalEqual(self):
        return bool(self._rotationCompare())

    def _evalDelta(self):
        return self._rotationCompare()

    def _evalVariance(self):
        return self._rotationCompare()


class EvaluationVector(EvaluationObj):
    """
    | Derived object for handling Math.SOA_Py.SOAVector evaluations.
    """

    def __init__(self, expected_vector, actual_vector, delta, delta_variance):
        EvaluationObj.__init__(self, expected_vector, actual_vector, delta, delta_variance)

    def _evalEqual(self):
        return bool(self.getDifference(self._expected_value, self._actual_value).magnitude() == 0)

    def _evalDelta(self):
        return fabs(self.getDifference(self._expected_value, self._actual_value).magnitude()) <= self._delta

    def _evalVariance(self):
        return fabs(self.getVariance(self._expected_value, self._actual_value)) <= self._delta_variance
