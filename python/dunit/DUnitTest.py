"""
DUnit extends and uses the native python unittest framework. DUnit is a
specialized unit tester facilitating the collection of evaluation results
and its requirement identifier at the evaluation statement rather than the
method.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import datetime
import inspect
import sys
import re
import unittest

from unittest import case

from math import fabs

from Dtest.dunit.DUnitFactoryEvaluation import FactoryEvaluation
from Dtest.dunit.DUnitFactoryResult import FactoryResult, ResultObjSpecial

if sys.version_info.major >= 3:
    str_types = (bytes, str)
else:
    str_types = (str, unicode)

# lambda expression
# TODO Convert this to a 'def' for pep8
RequirementIdentifier = lambda req: str(inspect.currentframe().f_back.f_lineno) + ":" + req
"""
Lambda expression used to retrieve the line number in the file where the
expression is invoked.
"""


class DUnit(unittest.TestCase):
    """
    DUnit extends and uses the native python unittest framework. DUnit is a
    specialized unit tester facilitating the collection of evaluation results
    and its requirement identifier at the evaluation statement rather than
    the method.
    """

    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)

        value = str(self.id()).split(".")

        self._evalModuleName = value[0]
        self._evalClassName = value[1]

        self._evalNow = str(datetime.date.today())

        if len(sys.argv) > 0:
            for item in sys.argv:
                if str(item).rfind(".py") >= 0:
                    item = str(item)

                    if item.rfind("/") >= 0:
                        self._evalModuleName = item[item.rfind("/") + 1 :]
                    else:
                        self._evalModuleName = item

        self._evalFailCount = 0
        self._lastError = ""

    def _evalAssertPass(self):
        """
        Fails the test case if any evaluation statements failed for the test
        case (e.g. test method). Raises an exception understood by Python
        unitttest that flags the test case as an unittest assert statement
        would.
        """
        if not (self._evalFailCount == 0):
            outString = self._testMethodName + ": Test Case Failure, " + str(self._evalFailCount)
            if self._evalFailCount == 1:
                outString += " statement failed"
            elif self._evalFailCount > 1:
                outString += " statements failed"
            raise self.failureException(outString)

    def _evalExecFileOut(self, outString):
        """
        Writes output to a file, formatting the output as necessary.
        """
        if self._evalFileOut is True:
            self._evalOutFile.write(outString + "\n")
            self._evalOutFile.flush()

    def _evalExecStdOut(self, outString, evalResult):
        """
        Writes output to the console, formatting the output as necessary.
        """
        if self._evalStdOut is True:
            if self._evalStdOutOnlyFail is True and evalResult is False:
                print(
                    "Line:",
                    outString.split(":")[4],
                    ":",
                    outString.split(":")[7],
                )
            elif self._evalStdOutOnlyFail is False:
                print(outString)

    def _evalMessage(self, requirementIdentifier):
        """
        Formats the requirement identifier and adds additional
        stratification information (e.g. date collected, file/module name,
        class name, method name, line number, requirement identifier).
        """
        # Comment: Results data format:  DateCollected:FileName/ModuleName:
        # ClassName:MethodName:LineNumber:RequirementIdentifier:Result
        return (
            self._evalNow
            + ":"
            + self._evalModuleName
            + ":"
            + self._evalClassName
            + ":"
            + self._testMethodName
            + ":"
            + requirementIdentifier
            + ":"
        )

    def _getEvalResult(
        self,
        requirementIdentifier,
        expectedValue,
        actualValue,
        delta,
        deltaVariance,
        quaternionRotation,
        msg,
        collect,
        bypass,
        resultObjSpecial,
    ):
        """
        Creates a Result object from the factory and uses it to make a
        comparison and generate output as applicable.
        Returns the Result object's evaluation boolean value as determined
        by the comparison.
        """

        import sys

        sys.expectedValue = expectedValue
        sys.actualValue = actualValue
        # Regularize spaces in arrays to be consistent across sites
        if isinstance(expectedValue, str_types):
            arr_re = re.compile(r"\[([-\+ 0-9\.,]+)\]")
            space_re = re.compile(r"\s+")

            mev = arr_re.findall(expectedValue)
            for old_arr_str in mev:
                arr_str = space_re.sub(" ", old_arr_str).strip()
                expectedValue = expectedValue.replace(old_arr_str, arr_str)

            mav = arr_re.findall(actualValue)
            for old_arr_str in mav:
                arr_str = space_re.sub(" ", old_arr_str).strip()
                actualValue = actualValue.replace(old_arr_str, arr_str)

            expectedValue = re.sub(r"array\(([0-9]*)\.\)", "array(\\1.0)", expectedValue)
            actualValue = re.sub(r"array\(([0-9]*)\.\)", "array(\\1.0)", actualValue)
        eval_msg = self._evalMessage(requirementIdentifier)
        e = FactoryResult.newResultObj(
            eval_msg,
            expectedValue,
            actualValue,
            delta,
            deltaVariance,
            quaternionRotation,
            msg,
            collect,
            bypass,
            resultObjSpecial,
        )

        if e.doCollect():
            outString = e.getOutString()
            self._evalExecFileOut(outString)

            if not e.doBypass():
                self._evalExecStdOut(outString, e.getEvalResult())

                if not e._eval_result:
                    self._evalFailCount += 1
                    self._lastError = e.getErrorMsg()

        return e._eval_result

    def evalEqual(
        self,
        requirementIdentifier,
        expectedValue,
        actualValue,
        msg=None,
        collect=True,
        bypass=False,
    ) -> bool:
        """
        Compares the expectedValue to the actualValue.
        Supports comparisons between alphanumeric values, SOAMatrix33
        objects, SOAMatrix44 objects, SOAQuaternion objects, and
        SOAVector3 objects.
        Supports comparisons between lists of alphanumeric values,
        SOAMatrix33 objects, SOAMatrix44 objects, SOAQuaternion objects,
        and SOAVector3 objects.

        The msg (message/note) is optional, and defaults to None.

        Returns True if the comparison is an exact match, else returns False.
        """
        return bool(
            self._getEvalResult(
                requirementIdentifier,
                expectedValue,
                actualValue,
                None,
                None,
                False,
                msg,
                collect,
                bypass,
                None,
            )
        )

    def evalEqualDelta(
        self,
        requirementIdentifier,
        expectedValue,
        actualValue,
        delta=1e-6,
        msg=None,
        collect=True,
        bypass=False,
    ) -> bool:
        """
        Compares the difference between the expectedValue and the
        actualValue to the delta.
        Supports comparisons between numeric values, SOAMatrix33 objects,
        SOAMatrix44 objects, SOAQuaternion objects, and SOAVector3 objects.
        Supports comparisons between lists of numeric values,
        SOAMatrix33 objects, SOAMatrix44 objects, SOAQuaternion objects,
        and SOAVector3 objects.

        The delta is optional, and defaults to 1e-6.
        The msg (message/note) is optional, and defaults to None.

        Returns True if the difference is less than or equal to the delta,
        else returns False.
        """
        delta = fabs(float(delta))
        return bool(
            self._getEvalResult(
                requirementIdentifier,
                expectedValue,
                actualValue,
                delta,
                None,
                False,
                msg,
                collect,
                bypass,
                None,
            )
        )

    def evalEqualDeltaRotation(
        self,
        requirementIdentifier,
        expectedValue,
        actualValue,
        delta=10e-12,
        msg=None,
        collect=True,
        bypass=False,
    ) -> bool:
        """
        Compares the difference between the expectedValue and the
        actualValue to the delta after executing a unit transformation.
        Will test for equivalent but non-identical rotations.
        Supports comparisons between SOAQuaternion objects.
        Supports comparisons between lists of SOAQuaternion objects.

        The delta is optional, and defaults to 10e-12.
        The msg (message/note) is optional, and defaults to None.

        Returns True if the difference is less than or equal to the delta,
        else returns False.
        """
        delta = fabs(float(delta))
        return bool(
            self._getEvalResult(
                requirementIdentifier,
                expectedValue,
                actualValue,
                delta,
                None,
                True,
                msg,
                collect,
                bypass,
                None,
            )
        )

    def evalEqualDeltaEuler(
        self,
        requirementIdentifier,
        expectedValue,
        actualValue,
        soaEulerSequence,
        delta=10e-12,
        msg=None,
        collect=True,
        bypass=False,
    ) -> bool:
        """
        Compares the difference between the expectedValue and the
        actualValue to the delta after converting it via the
        soaEulerSequence and executing a unit transformation.
        Will test for equivalent but non-identical rotations.
        Supports comparisons between SOAVector objects converted via the
        soaEulerSequence.
        Supports comparisons between lists of SOAQuaternion objects
        converted via the soaEulerSequence.

        The delta is optional, and defaults to 10e-12.
        The msg (message/note) is optional, and defaults to None.

        Returns True if the difference is less than or equal to the delta,
        else returns False.
        """
        # Due to SOA changes in JPL BasePkg R6-00a, need to de-reference the
        # values returned from FactorySoa in order for the _getEvalResult
        # call to work.
        from Dtest.dunit.DUnitFactorySoa import FactorySoa

        expectedValue = FactorySoa.newQuaternionFromEuler(
            expectedValue[0],
            expectedValue[1],
            expectedValue[2],
            soaEulerSequence,
        )()
        actualValue = FactorySoa.newQuaternionFromEuler(
            actualValue[0], actualValue[1], actualValue[2], soaEulerSequence
        )()

        delta = fabs(float(delta))
        return bool(
            self._getEvalResult(
                requirementIdentifier,
                expectedValue,
                actualValue,
                delta,
                None,
                True,
                msg,
                collect,
                bypass,
                None,
            )
        )

    def evalEqualVariance(
        self,
        requirementIdentifier,
        expectedValue,
        actualValue,
        deltaVariance=0.1,
        msg=None,
        collect=True,
        bypass=False,
    ) -> bool:
        """
        Compares the variance between the expectedValue and the actualValue
        to the delta variance.
        Supports comparisons between numeric values, SOAMatrix33 objects,
        SOAMatrix44 objects, SOAQuaternion objects, and SOAVector3 objects.
        Supports comparisons between lists of numeric values,
        SOAMatrix33 objects, SOAMatrix44 objects, SOAQuaternion objects,
        and SOAVector3 objects.

        The deltaVariance is optional, and defaults to 0.1 (10%).
        The msg (message/note) is optional, and defaults to None.

        Returns True if the variance is less than or equal to the
        deltaVariance, else returns False.
        """
        deltaVariance = fabs(float(deltaVariance))
        return bool(
            self._getEvalResult(
                requirementIdentifier,
                expectedValue,
                actualValue,
                None,
                deltaVariance,
                False,
                msg,
                collect,
                bypass,
                None,
            )
        )

    def evalExpTrue(
        self,
        requirementIdentifier,
        actualBool,
        msg=None,
        collect=True,
        bypass=False,
    ) -> bool:
        """
        Compares the expected True boolean to the actualBool value.
        actualBool can be any expression that evaluates to a Boolean value,
        including a Boolean variable. This includes greater/less than, etc.

        The msg (message/note) is optional, and defaults to None.

        Returns True if the provided expression evaluates to True, else
        returns False.
        """
        return bool(
            self._getEvalResult(
                requirementIdentifier,
                True,
                actualBool,
                None,
                None,
                False,
                msg,
                collect,
                bypass,
                None,
            )
        )

    def evalExpFalse(
        self,
        requirementIdentifier,
        actualBool,
        msg=None,
        collect=True,
        bypass=False,
    ) -> bool:
        """
        Compares the expected False boolean to the actualBool value.
        actualBool can be any expression that evaluates to a Boolean value,
        including a Boolean variable. This includes greater/less than, etc.

        The msg (message/note) is optional, and defaults to None.

        Returns True if the provided expression evaluates to False, else
        returns False.
        """
        return bool(
            self._getEvalResult(
                requirementIdentifier,
                False,
                actualBool,
                None,
                None,
                False,
                msg,
                collect,
                bypass,
                None,
            )
        )

    def evalCustom(self, requirementIdentifier, msg=None, collect=True):
        """
        Facilitates the use of documenting CUSTOM requirements.
        Used to document requirements that are implemented via
        Customer-specific Code.  The requirement
        may either be implemented in the future or categorized as a
        Plan-Train-Fly requirement
        to be implemented by the user community.

        The msg (message/note) is optional, and defaults to None.

        Returns True.
        """
        bypass = True
        return self._getEvalResult(
            requirementIdentifier,
            None,
            None,
            None,
            None,
            False,
            msg,
            collect,
            bypass,
            ResultObjSpecial.Custom,
        )

    def evalMissing(self, requirementIdentifier, msg=None, collect=True, bypass=False):
        """
        Facilitates the use of documenting MISSING requirements.
        Used to document requirements that are missing from the
        implementation, or unable to locate the requirement within the
        implementation.

        The msg (message/note) is optional, and defaults to None.

        Returns True.
        """
        return self._getEvalResult(
            requirementIdentifier,
            None,
            None,
            None,
            None,
            False,
            msg,
            collect,
            bypass,
            ResultObjSpecial.Missing,
        )

    def evalSatisfied(self, requirementIdentifier, msg=None, collect=True, bypass=False):
        """
        Facilitates the use of documenting SATISFIED requirements.
        Used to document requirements that is fulfilled implicitly through
        the nature of the simulation or the run-deck.

        The msg (message/note) is optional, and defaults to None.

        Returns True.
        """
        return self._getEvalResult(
            requirementIdentifier,
            None,
            None,
            None,
            None,
            False,
            msg,
            collect,
            bypass,
            ResultObjSpecial.Satisfied,
        )

    def evalUncertain(self, requirementIdentifier, msg=None, collect=True, bypass=False):
        """
        Facilitates the use of documenting UNCERTAIN requirements.
        Used to document requirement uncertainty; such as whether the
        identified requirement implementation is the same as the documented
        requirement, or there is not enough understanding of the domain
        knowledge driving the requirement, or unsure is test is adequate
        for requirement.

        The msg (message/note) is optional, and defaults to None.

        Returns True.
        """
        return self._getEvalResult(
            requirementIdentifier,
            None,
            None,
            None,
            None,
            False,
            msg,
            collect,
            bypass,
            ResultObjSpecial.Uncertain,
        )

    def evalUnverifiable(self, requirementIdentifier, msg=None, collect=True, bypass=False):
        """
        Facilitates the use of documenting UNVERIFIABLE requirements.
        Used to document requirement is unverifiable; such as unable to
        verify requirement as written (e.g. poorly written requirement,
        ambiguous requirement, requirement not testable), or as implemented
        (e.g. not implemented in the spirit of the requirement).

        The msg (message/note) is optional, and defaults to None.

        Returns True.
        """
        return self._getEvalResult(
            requirementIdentifier,
            None,
            None,
            None,
            None,
            False,
            msg,
            collect,
            bypass,
            ResultObjSpecial.Unverifiable,
        )

    def addToXml(self, isPassing):
        """
        XML Conversion (fix this up)
        """
        info = str(self.id()).split(".")

        xmlString = '\n  <testcase classname="' + info[0] + "." + info[1] + '" name="' + info[2] + '" time="0.0000">'
        if isPassing:
            xmlString += "</testcase>"
        else:
            xmlString += (
                '\n    <failure type="exceptions.AssertionError"'
                + "><![CDATA["
                + self._lastError
                + "]]></failure>\n  </testcase>"
            )
        return xmlString

    @classmethod
    def setUpClass(cls):
        """
        Overwrites the existing unittest.setUpClass() method enabling the
        collection of DUnittest arguments.
        If the user of this class overrides the DUnit.setUpClass() method,
        the user must include a statement invoking the DUnit.setUpClass()
        base method.
        """
        cls._evalDUnitDebug = False

        cls._evalFileOut = False
        cls._evalXmlOut = False
        cls._evalStdOut = False
        cls._evalStdOutOnlyFail = False

        cls._isEvalAssertPass = True

        for item in sys.argv:

            if item == "evalFileOut=True":
                cls._evalFileOut = True
                cls._evalXmlOut = True
                continue

            if item == "evalStdOut=True":
                cls._evalStdOut = True
                continue

            if item == "evalStdOutOnlyFail=True":
                cls._evalStdOutOnlyFail = True
                continue

            if item == "isEvalAssertPass=False":
                cls._isEvalAssertPass = False
                continue

        if cls._evalFileOut is True:
            cls._evalOutFile = open("outResults.dat", "a")
            cls._evalXmlFile = open("outResults.xml", "a")

    def tearDown(self):
        """
        Overrides the existing unittest.tearDown() method, then inserts a
        method invocation to DUnit._evalAssertPass() to achieve unittest
        "failure status" reporting, and then calls the native
        unittest.tearDown() class method.
        If the user of this class overrides the DUnit.tearDown() method,
        the user must include a statement invoking the DUnit.tearDown()
        base method.
        """
        if self._isEvalAssertPass:
            self._evalAssertPass()

        unittest.TestCase.tearDown(self)
