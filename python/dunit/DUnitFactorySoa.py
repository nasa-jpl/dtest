"""
FactorySoa is a factory-based object used to create Math.SOA_Py objects.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from Math.SOA_Py import SOAVector4
from Math.SOA_Py import SOAQuaternion
from Math.SOA_Py import SOAEuler


class FactorySoa:
    """
    FactorySoa is a factory-based object used to create Math.SOA_Py objects.
    """

    @staticmethod
    def newQuaternion(value1, value2=None, value3=None, value4=None):
        """
        | Factory method that creates a Math.SOA_Py.SOAQuaternion object from
        | values.
        | Supports creating the SOAQuaternion from a SOAVector4,
        | SOAQuaternion, a list of four values, a tuple of four values, and
        | four separate values.
        |
        | Returns a Math.SOA_Py.SOAQuaternion object.
        """
        soaVector4 = None

        if isinstance(value1, SOAVector4):
            soaVector4 = value1

        elif isinstance(value1, SOAQuaternion):
            soaVector4 = value1.vec4()

        else:
            soaVector4 = FactorySoa.newVector4(value1, value2, value3, value4)

        # Changes in JPL BasePkg R6-00a no longer allows for
        # SOAVector ne (!=) operation with None
        if soaVector4.size() == 4:
            soaVector4.normalize()
            return SOAQuaternion(soaVector4)
        else:
            return None

    @staticmethod
    def newQuaternionFromEuler(value1, value2, value3, soaEulerSequence):
        """
        | Factory method that creates a Math.SOA_Py.SOAQuaternion object from
        | three separate values and the Euler sequence specified.
        |
        | Returns a Math.SOA_Py.SOAQuaternion object.
        """
        try:
            return SOAQuaternion(SOAEuler(value1, value2, value3, soaEulerSequence))
        except:
            return None

    @staticmethod
    def newVector3(value1, value2=None, value3=None):
        pass

    @staticmethod
    def newVector4(value1, value2=None, value3=None, value4=None):
        """
        | Factory method that creates a Math.SOA_Py.SOAVector4 object from
        | values.
        | Supports creating the SOAVector4 from a list of four values, a
        | tuple of four values, and four separate values.
        |
        | Returns a Math.SOA_Py.SOAVector4 object.
        """

        if isinstance(value1, list) or isinstance(value1, tuple):
            return SOAVector4(value1[0], value1[1], value1[2], value1[3])

        try:
            return SOAVector4(value1, value2, value3, value4)
        except:
            pass

        return None
