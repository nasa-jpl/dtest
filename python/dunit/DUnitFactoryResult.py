"""
FactoryResult is a factory-based object used to create ResultObj objects.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from Dtest.dunit.DUnitFactoryEvaluation import FactoryEvaluation


class ResultObjSpecial:
    """
    Object used for ResultObj special case enumeration.
    """

    Custom = "CUSTOM"
    Missing = "MISSING"
    Satisfied = "SATISFIED"
    Uncertain = "UNCERTAIN"
    Unverifiable = "UNVERIFIABLE"


class FactoryResult:
    """
    FactoryResult is a factory-based object used to create ResultObj
    objects.
    """

    @staticmethod
    def _verifyListObjects(expected_value, actual_value):
        if isinstance(expected_value, tuple):
            expected_value = list(expected_value)

        if isinstance(actual_value, tuple):
            actual_value = list(actual_value)

        if isinstance(expected_value, list):
            if isinstance(actual_value, list):
                return True
        return False

    @staticmethod
    def newResultObj(
        requirement_identifier,
        expected_value,
        actual_value,
        delta=None,
        delta_variance=None,
        quaternion_rotation=False,
        msg=None,
        collect=True,
        bypass=False,
        result_obj_special=None,
    ):
        """
        | Factory method that creates a ResultObj object from values.
        """
        if result_obj_special is not None:
            return ResultSpecial(requirement_identifier, msg, collect, bypass, result_obj_special)

        if FactoryResult._verifyListObjects(expected_value, actual_value) is True:
            if (delta is None) and (delta_variance is None):
                return ResultEqualLists(
                    requirement_identifier,
                    expected_value,
                    actual_value,
                    msg,
                    collect,
                    bypass,
                )

            if (delta is not None) and (delta_variance is None):
                return ResultDeltaLists(
                    requirement_identifier,
                    expected_value,
                    actual_value,
                    delta,
                    quaternion_rotation,
                    msg,
                    collect,
                    bypass,
                )

            if (delta is None) and (delta_variance is not None):
                return ResultVarianceLists(
                    requirement_identifier,
                    expected_value,
                    actual_value,
                    delta_variance,
                    msg,
                    collect,
                    bypass,
                )

        if FactoryResult._verifyListObjects(expected_value, actual_value) is False:
            if (delta is None) and (delta_variance is None):
                return ResultEqual(
                    requirement_identifier,
                    expected_value,
                    actual_value,
                    msg,
                    collect,
                    bypass,
                )

            if (delta is not None) and (delta_variance is None):
                return ResultDelta(
                    requirement_identifier,
                    expected_value,
                    actual_value,
                    delta,
                    quaternion_rotation,
                    msg,
                    collect,
                    bypass,
                )

            if (delta is None) and (delta_variance is not None):
                return ResultVariance(
                    requirement_identifier,
                    expected_value,
                    actual_value,
                    delta_variance,
                    msg,
                    collect,
                    bypass,
                )

        return None


class ResultObj:
    """
    Base object containing common information usable by derived classes.
    """

    def __init__(
        self,
        requirement_identifier,
        expected_value,
        actual_value,
        delta,
        delta_variance,
        quaternion_rotation,
        msg,
        collect,
        bypass,
        result_obj_special,
    ):
        self._requirement_identifier = requirement_identifier
        self._expected_value = expected_value
        self._actual_value = actual_value
        self._delta = delta
        self._delta_variance = delta_variance

        self._msg = msg
        self._collect = collect
        self._bypass = bypass
        self._result_obj_special = result_obj_special
        self._quaternion_rotation = quaternion_rotation

        self._msg_failure = None
        self._eval_result = self._evaluateResult()

    def _evaluateResult(self):
        e = FactoryEvaluation.newEvaluationObj(
            self._expected_value,
            self._actual_value,
            self._delta,
            self._delta_variance,
            self._quaternion_rotation,
        )

        if e is not None:
            eval_result = e.performEvaluation()
            if eval_result is False:
                self._msg_failure = str(self._expected_value) + " != " + str(self._actual_value)
            return eval_result
        else:
            return False

    def _getFormattedFailureString(self):
        pass

    def _getOutString(self, additional_description):
        out_string = self._requirement_identifier

        if self._eval_result:
            out_string += "PASS::"
        else:
            out_string += "FAIL:"
            msg_failure = self._msg_failure
            if msg_failure is None:
                msg_failure = ""
            out_string += msg_failure + additional_description + ":"

        out_string += str(self._msg)
        return out_string

    def doBypass(self):
        """
        Returns the boolean value of _bypass.
        """
        return self._bypass

    def doCollect(self):
        """
        Returns the boolean value of _collect.
        """
        return self._collect

    def getEvalResult(self):
        """
        Return the boolean value of evaluation result.
        """
        return self._eval_result

    def getOutString(self):
        """
        Virtual method.
        """
        pass

    def getErrorMsg(self):
        """
        Return the error message.
        """
        out_string = ""
        if self._msg_failure is not None:
            out_string = out_string + self._msg_failure + " "
        if self._msg is not None:
            out_string = out_string + self._msg
        return out_string


class ResultObjLists(ResultObj):
    """
    Base object containing common information usable by derived classes for
    supporting lists of objects.
    """

    def __init__(
        self,
        requirement_identifier,
        expected_value,
        actual_value,
        delta,
        delta_variance,
        quaternion_rotation,
        msg,
        collect,
        bypass,
    ):
        ResultObj.__init__(
            self,
            requirement_identifier,
            expected_value,
            actual_value,
            delta,
            delta_variance,
            quaternion_rotation,
            msg,
            collect,
            bypass,
            None,
        )

    def _evaluateResult(self):
        if self.evalVerifyListLengths(self._expected_value, self._actual_value) is False:
            self._msg_failure = "Lists are not equal length."
            return False

        eval_result = True
        list_fail = []

        for index in range(len(self._expected_value)):
            ev = self._expected_value[index]
            av = self._actual_value[index]
            e = FactoryEvaluation.newEvaluationObj(
                ev,
                av,
                self._delta,
                self._delta_variance,
                self._quaternion_rotation,
            )
            if e is not None:
                if e.performEvaluation() is False:
                    ev = self._expected_value[index]
                    av = self._actual_value[index]
                    list_fail.append(self._getFormattedFailureString(ev, av, index))
                    eval_result = False
            else:
                eval_result = False

        if len(list_fail) > 0:
            for index in range(len(list_fail)):
                if self._msg_failure is None:
                    self._msg_failure = list_fail[index]
                else:
                    self._msg_failure += ", " + list_fail[index]

            self._msg_failure = "[" + self._msg_failure + "]"

        return eval_result

    def _getFormattedFailureString(self, expected_value, actual_value, index):
        return "[" + str(index) + "] " + str(expected_value) + " != " + str(actual_value)

    @staticmethod
    def evalVerifyListLengths(expected_list, actual_list):
        """
        Compares the length of the expected_list to the length of the
        actual_list.

        Returns True if the lengths are equal, else returns False.
        """
        return len(expected_list) == len(actual_list)


class ResultEqual(ResultObj):
    """
    Derived object for handling equal evaluations.
    """

    def __init__(
        self,
        requirement_identifier,
        expected_value,
        actual_value,
        msg,
        collect,
        bypass,
    ):
        ResultObj.__init__(
            self,
            requirement_identifier,
            expected_value,
            actual_value,
            None,
            None,
            None,
            msg,
            collect,
            bypass,
            None,
        )

    def getOutString(self):
        """
        Returns a resultant string formatted specifically for equal
        evaluations.
        """
        return self._getOutString("")


class ResultDelta(ResultObj):
    """
    Derived object for handling delta evaluations.
    """

    def __init__(
        self,
        requirement_identifier,
        expected_value,
        actual_value,
        delta,
        quaternion_rotation,
        msg,
        collect,
        bypass,
    ):
        ResultObj.__init__(
            self,
            requirement_identifier,
            expected_value,
            actual_value,
            delta,
            None,
            quaternion_rotation,
            msg,
            collect,
            bypass,
            None,
        )

    def getOutString(self):
        """
        Returns a resultant string formatted specifically for delta
        evaluations.
        """
        return self._getOutString(" within " + str(self._delta))


class ResultVariance(ResultObj):
    """
    Derived object for handling variance evaluations.
    """

    def __init__(
        self,
        requirement_identifier,
        expected_value,
        actual_value,
        delta_variance,
        msg,
        collect,
        bypass,
    ):
        ResultObj.__init__(
            self,
            requirement_identifier,
            expected_value,
            actual_value,
            None,
            delta_variance,
            None,
            msg,
            collect,
            bypass,
            None,
        )

    def getOutString(self):
        """
        Returns a resultant string formatted specifically for variance
        evaluations.
        """
        out_delta_variance = "%f" % (self._delta_variance * 100)
        return self._getOutString(" within " + out_delta_variance + " %")


class ResultEqualLists(ResultObjLists):
    """
    Derived object for handling a list of equal evaluations.
    """

    def __init__(
        self,
        requirement_identifier,
        expected_value,
        actual_value,
        msg,
        collect,
        bypass,
    ):
        ResultObjLists.__init__(
            self,
            requirement_identifier,
            expected_value,
            actual_value,
            None,
            None,
            None,
            msg,
            collect,
            bypass,
        )

    def getOutString(self):
        """
        Returns a resultant string formatted specifically for a list of
        equal evaluations.
        """
        return self._getOutString("")


class ResultDeltaLists(ResultObjLists):
    """
    Derived object for handling a list of delta evaluations.
    """

    def __init__(
        self,
        requirement_identifier,
        expected_value,
        actual_value,
        delta,
        quaternion_rotation,
        msg,
        collect,
        bypass,
    ):
        ResultObjLists.__init__(
            self,
            requirement_identifier,
            expected_value,
            actual_value,
            delta,
            None,
            quaternion_rotation,
            msg,
            collect,
            bypass,
        )

    def getOutString(self):
        """
        Returns a resultant string formatted specifically for a list of
        delta evaluations.
        """
        return self._getOutString(" within " + str(self._delta))


class ResultVarianceLists(ResultObjLists):
    """
    Derived object for handling a list of variance evaluations.
    """

    def __init__(
        self,
        requirement_identifier,
        expected_value,
        actual_value,
        delta_variance,
        msg,
        collect,
        bypass,
    ):
        ResultObjLists.__init__(
            self,
            requirement_identifier,
            expected_value,
            actual_value,
            None,
            delta_variance,
            None,
            msg,
            collect,
            bypass,
        )

    def getOutString(self):
        """
        Returns a resultant string formatted specifically for a list of
        variance evaluations.
        """
        out_delta_variance = "%f" % (self._delta_variance * 100)
        return self._getOutString(" within " + str(out_delta_variance))


class ResultSpecial(ResultObj):
    """
    Derived object for handling special case evaluations.
    """

    def __init__(self, requirement_identifier, msg, collect, bypass, result_obj_special):
        ResultObj.__init__(
            self,
            requirement_identifier,
            None,
            None,
            None,
            None,
            None,
            msg,
            collect,
            bypass,
            result_obj_special,
        )

    def _evaluateResult(self):
        return True

    def getOutString(self):
        """
        Returns a resultant string formatted specifically for special case
        evaluations.
        """
        return self._requirement_identifier + self._result_obj_special + "::" + str(self._msg)
