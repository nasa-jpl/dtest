"""DCompareUtils.py.

Utility classes and functions to compare files for regression tests.


By: Jonathan M. Cameron (March 2008)
    Extensions by Abhi Jain

"""

from __future__ import division
from __future__ import absolute_import
from __future__ import print_function

import re
import os
import sys
from math import fabs

try:
    basestring
except NameError:
    basestring = str

# floats comparison returns true if the numbers are essentially zero or
# else if the relative error is less than the relative tolerance

global abseps, releps

# numbers less than this are treated as 0
abseps = 1.0e-12

# relative tolerance to
releps = 1.0e-10


def _formatFloat(f):
    """Formats a float consistently across Python2 and 3. This should
    have an identical result to str(f) in Python2.

    """
    return "%.12g" % f


# get the path prefixes to ignore
def getFileCompareIgnorePathPrefixes():
    """Get/construct the path prefixes to ignore in Dtest comparisons"""
    env_ignores = os.getenv("DTEST_IGNORE_PATH_PREFIXES", None)
    if env_ignores:
        ignores = env_ignores.split(",")
    else:
        ignores = ["/home/"]
    return ignores


IGNORE_STRING_PREFIXES = getFileCompareIgnorePathPrefixes()


def cmpPair(x, y, path=""):
    """Compare two objects silently, allowing small differences in floating
    point numbers.

    @param x : one object
    @param y : another object to compare with
    @return: True if they are the same, False if not

    """
    if isinstance(x, dict):
        if isinstance(y, dict):
            return cmpDicts(x, y, path)
        else:
            return False
    elif isinstance(x, int) and isinstance(y, int):
        if x != y:
            return False
    elif isinstance(x, basestring):
        if _stringIsIgnored(x) or _stringIsIgnored(y):
            return True
        if x != y:
            return False
    elif isinstance(x, list) or isinstance(x, tuple):
        for i in range(0, len(x)):
            if cmpPair(x[i], y[i], path) is False:
                return False
    else:
        try:
            fx = float(x)
            fy = float(y)
            delta = fabs(fx - fy)
            # return true if either the delta error is less than the
            # absolute tolerance, or if the relative error is less than
            # the relative tolerance
            if fabs(x) < abseps:
                # x is essentially zero
                return delta < abseps
            else:
                # x is non-zero, so check relative tolerance
                return delta / fabs(x) < releps
        except:
            if x != y:
                return False
    return True


def cmpDicts(a, b, path=""):
    """Compare two dictionaries, allowing small differences in floating point
    numbers (set up eps).

    @param a : one dictionary
    @param b : another dictionary to compare with
    @return: True if the dictionaries match, False if not

    """
    # check that a & b have exactly the same keys
    if set(a.keys()).difference(set(b.keys())):
        return False
    if set(b.keys()).difference(set(a.keys())):
        return False

    # Compare the values of all keys
    for k in a.keys():
        if k in b.keys():
            aval = a[k]
            bval = b[k]
            if not cmpPair(aval, bval, "%s.%s" % (path, k)):
                return False
        else:
            return False

    return True


def cmpPairVerbose(x, y, path=""):
    """Compare two objects and display differences - allowing small differences
    in floating point numbers.

    There is no return value.
    @param x : one object
    @param y : another object to compare with

    """
    if isinstance(x, dict):
        if isinstance(y, dict):
            cmpDictsVerbose(x, y, path)
        else:
            print("* Not a dictionary %s on Right:" % path.lstrip("."), y)
    elif isinstance(x, int) and isinstance(y, int):
        if x != y:
            print("* %s:" % path.lstrip("."), x, "vs", y)
    elif isinstance(x, basestring):
        if _stringIsIgnored(x):
            return True
        elif isinstance(y, basestring) and _stringIsIgnored(y):
            return True
        if x != y:
            print("* Difference at dict[%s] ==> " % (path.lstrip(".")))
            print("     Left: '%s'" % (x))
            print("     Right: '%s'" % (y))
    elif isinstance(x, list) or isinstance(x, tuple):
        for i in range(0, len(x)):
            cmpPairVerbose(x[i], y[i], path)
    else:
        try:
            fx = float(x)
            fy = float(y)
            delta = fabs(fx - fy)
            # return true if the relative error is less than the
            # relative tolerance, i.e. or is the numbers are essentially zero
            if fabs(x) < abseps:
                # x is essentially 0
                if delta >= abseps:
                    print("* %s:" % path.lstrip("."), x, "vs", y)
            elif delta / fabs(x) >= releps:
                # x is non-zero, so check relative tolerance
                print(
                    "* %s:" % path.lstrip("."),
                    _formatFloat(x),
                    "vs",
                    _formatFloat(y),
                    "rel=",
                    _formatFloat(delta / fabs(x)),
                )
        except:
            if x != y:
                print(
                    "Difference at dict[%s] ==> Left:" % path.lstrip("."),
                    x,
                    " Right:",
                    y,
                )


def cmpDictsVerbose(a, b, path=""):
    """Compare two dictionaries and display difference - allowing small
    differences in floating point numbers (set up eps).

    There is no
    return value.
    @param a : one dictionary
    @param b : another dictionary to compare with

    """
    # check that a & b have exactly the same keys
    if set(a.keys()).difference(set(b.keys())):
        print(
            "Extra keys on Left at dict[%s] ==> " % path.lstrip("."),
            list(set(a.keys()).difference(set(b.keys()))),
        )
    if set(b.keys()).difference(set(a.keys())):
        print(
            "Extra keys on Right at dict[%s] ==>:" % path.lstrip("."),
            list(set(b.keys()).difference(set(a.keys()))),
        )

    # Compare the values of all keys
    for k in a.keys():
        if k in b.keys():
            aval = a[k]
            bval = b[k]
            cmpPairVerbose(aval, bval, "%s.%s" % (path, k))


def cmpModelFiles(f1name, f2name, verbose, new_abs_eps=None, new_rel_eps=None):
    """Compare two model files, allowing small differences in floating point
    numbers (set up eps).

    @param f1name : one model file
    @param f2name : another model file to compare with
    @param verbose : Print out extra information about differences
    @param new_abs_eps : New absolute tolerance to use (default is 1.0e-12)
    @param new_rel_eps : New relative tolerance to use if both numbers are not
                         small (default is 1.0e-10)

    @return: True if the model files match, False if not

    """

    # Update the tolerances (if requested)
    global abseps, releps
    if new_abs_eps:
        abseps = new_abs_eps
    if new_rel_eps:
        releps = new_rel_eps

    # Read the files
    with open(f1name, "r") as f1:
        str1 = f1.read()
    str1 = str1.replace("\n", " ").strip()

    with open(f2name, "r") as f2:
        str2 = f2.read()
    str2 = str2.replace("\n", " ").strip()

    # Strip out any YAM_ROOT prefixes

    # Get the actual dictionary (file1)
    m1 = re.search(
        "(Assembly.createModelFromParam\\(|DshellObj.createDshellModelFromParam\\()(.*)\\)$",
        str1,
    )
    if m1:
        try:
            dict1 = eval(m1.group(2))
        except:
            sys.stderr.write("Error in left file %s: \n --> Error parsing " "%s dictionary\n" % (f1name, m1.group(1)))
            return False

    else:
        sys.stderr.write("Error in left file %s: \n --> Not a model file! " "(dictionary not found)\n" % f1name)
        return False

    # Get the actual dictionary (file2)
    m2 = re.search(
        "(Assembly.createModelFromParam\\(|DshellObj.createDshellModelFromParam\\()(.*)\\)$",
        str2,
    )
    if m2:
        try:
            dict2 = eval(m2.group(2))
        except:
            sys.stderr.write("Error in right file %s: \n --> Error parsing " "%s dictionary\n" % (f2name, m2.group(1)))
            return False
    else:
        sys.stderr.write("Error in right file %s: \n --> Not a model file! " "(dictionary not found)\n" % f2name)
        return False

    if verbose:
        cmpDictsVerbose(dict1, dict2)
    else:
        return cmpDicts(dict1, dict2)


def cmpDictsInFiles(
    f1name,
    f2name,
    start_re_str,
    end_re_str,
    whole_file=False,
    verbose=False,
    new_abs_eps=None,
    new_rel_eps=None,
):
    """Compare dictionaries in two files, allowing small differences in
    floating point numbers (set up eps).

    The dictionary in the files are between the start and end regular
    expressions as specified in the start_re_str and end_re_str.

    NOTE: The start_re and end_re should be one separate lines from the
    dictionary!

    @param f1name : one file
    @param f2name : another model file to compare with
    @param start_re_str : String to compile beginning regular expression from
    @param end_re_str : String to compile ending regular expression from
    @param whole_file : Assume each entire file is a single dictionary
                        (without any start_re or end_re)
    @param verbose : Print out extra information about differences
    @param new_abs_eps : New absolute tolerance to use (default is 1.0e-12)
    @param new_rel_eps : New relative tolerance to use if both numbers are
                         not small (default is 1.0e-10)

    @return: True if the model files match, False if not

    """

    def getDictionary(filename, start_re, end_re, whole_file=False):
        """Get the dictionary from the file."""

        new_dict = None

        if whole_file:

            dict_str = ""
            with open(filename, "r") as f:
                dict_str = f.read()

            # Strip off any leading 'x ='
            dict_start_re = re.compile(r"^([ \t]*[a-zA-Z0-9_]+[ \t]*=[ \t]*)")
            m = dict_start_re.match(dict_str)
            if m:
                dict_str = dict_str.replace(m.group(1), "", 1)

            try:
                new_dict = eval(dict_str)
            except:
                raise ValueError("Error evaluating dictionary in whole file %s" % filename)

        else:

            dict_str = ""
            start_line = None
            end_line = None
            before_dict = True
            line_num = 0

            dict_start_re = re.compile(r"^[ \t]*[a-zA-Z0-9_]+[ \t]*=[ \t]*(\{.*)$")

            for line in open(filename, "r"):
                line = line.strip()
                line_num += 1
                if before_dict:
                    if start_re.match(line):
                        start_line = line_num + 1
                        before_dict = False
                else:
                    if end_re.search(line):
                        end_line = line_num - 1
                        break

                    else:
                        if line_num == start_line:
                            # Strip off 'a =' from 'a = {' on first line of
                            # dictionary (if present)
                            m = dict_start_re.match(line)
                            if m:
                                dict_str = m.group(1)
                            else:
                                dict_str = line
                        else:
                            dict_str += "\n" + line

            if end_line is None:
                raise ValueError("End of dictonary in file '%s' not located by line %d" % (filename, line_num))
            else:
                try:
                    new_dict = eval(dict_str)
                except:
                    raise ValueError(
                        "Error evaluating dictionary in file %s " "(lines %d to %d)" % (filename, start_line, end_line)
                    )

        return new_dict

    # Update the tolerances (if requested)
    global abseps, releps
    if new_abs_eps:
        abseps = new_abs_eps
    if new_rel_eps:
        releps = new_rel_eps

    # Construct the regular expressions to bracket the dictionary
    start_re = re.compile(start_re_str)
    end_re = re.compile(end_re_str)

    # Get the dictionary from file1
    dict1 = getDictionary(f1name, start_re, end_re, whole_file)
    if dict1 is None:
        raise ValueError("Error in left file (%s): Unable to get dictionary!" % f1name)

    # Get the dictionary from file1
    dict2 = getDictionary(f2name, start_re, end_re, whole_file)
    if dict2 is None:
        raise ValueError("Error in right file (%s): Unable to get dictionary!" % f2name)

    # Do the comparison
    if verbose:
        cmpDictsVerbose(dict1, dict2)
    else:
        return cmpDicts(dict1, dict2)


def cmpCheckpointFiles(f1name, f2name, verbose, new_abs_eps=None, new_rel_eps=None):
    """Compare two checkpoint files, allowing small differences in floating
    point numbers.

    @param f1name : one checkpoint filename
    @param f2name : another checkpoint filename to compare with
    @param verbose : Print out extra information about differences
    @param new_abs_eps : New absolute tolerance to use (default is 1.0e-12)
    @param new_rel_eps : New relative tolerance to use if both numbers are
                         not small (default is 1.0e-10)

    @return: True if the chekpoint files match, False if not

    NOTE: This function assumes that the two files have exactly the
          same line layout.  This should probably be generalized.

    """

    def locateDicts(f, dname, start_re, end_re):
        """Locate the beginning and end of the dictionary parts."""
        dict_bounds = []
        start_line = None
        end_line = None
        before_dict = True
        line_num = 0
        f.seek(0)
        for line in f:
            line = line.strip()
            line_num += 1
            if before_dict:
                if start_re.match(line):
                    start_line = line_num
                    before_dict = False
            else:
                if line == "":
                    end_line = line_num - 1
                    dict_bounds.append((start_line, end_line))
                    before_dict = True
                else:
                    if end_re.search(line):
                        break

        if end_line is None:
            sys.stderr.write("End of %s dictonary not located by line %d\n" % (dname, line_num))
            print("Start of dictionary at", start_line, file=sys.stderr)

        f.seek(0)
        return dict_bounds

    def getDictStr(f, dname, dict_start, dict_end):
        """Extract the dictionary from the file."""
        f.seek(0)
        line = ""
        for _ in range(0, dict_start - 1):
            line = f.readline().strip()
        dstr = ""
        for _ in range(dict_start, dict_end + 1):
            line = f.readline().strip()
            dstr += " " + line
        return dstr.strip()

    def compareLines(f1, f2, start_line1, start_line2, num_lines):
        """Compare the specified lines textually (f1, f2 should be open file
        handles)."""
        # Start at the top of each file
        f1.seek(0)
        f2.seek(0)

        # Skip over the lines before the section
        for _ in range(0, start_line1):
            f1.readline()
        for _ in range(0, start_line2):
            f2.readline()

        # Compare the active lines
        for i in range(0, num_lines):
            line1 = f1.readline()
            line2 = f2.readline()
            if line1 == "" and line2 == "":
                break
            elif line1 == "" and line2 != "":
                if verbose:
                    print("%s is shorter than %s" % (f1name, f2name))
                else:
                    f1.close()
                    f2.close()
                    return False
            elif line1 != "" and line2 == "":
                if verbose:
                    print("%s is longer than %s" % (f1name, f2name))
                else:
                    f1.close()
                    f2.close()
                    return False
            line1 = line1.strip()
            line2 = line2.strip()
            if line1 != line2:
                if verbose:
                    print("Difference at line:")
                    print("%4d < " % (i + start_line1 + 1), line1)
                    print("%4d > " % (i + start_line2 + 1), line2)
                else:
                    f1.close()
                    f2.close()
                    return False
        return True

    def countLines(f):
        """Count the number of lines in the file."""
        f.seek(0)
        num_lines = 0
        for _ in f:
            num_lines += 1
        return num_lines

    # Update the tolerances (if requested)
    global abseps, releps
    if new_abs_eps:
        abseps = new_abs_eps
    if new_rel_eps:
        releps = new_rel_eps

    # define the regular expressions bounding each dictionary
    model_start_re = re.compile(r"Dvar_Py.getDvar|DshellObj.dvarContainer\(\).getDVar")
    model_end_re = re.compile(r"Model.modelObjFromUuid")
    mbody_start_re = re.compile(r"^DshellObj.mbody\(\).specNode\(\)")
    mbody_end_re = re.compile(r"^# Restore the signal values")

    # Open the files
    f1 = open(f1name, "r")
    f2 = open(f2name, "r")

    # Find the spacecraft model dictionaries
    model_dict_bounds1 = locateDicts(f1, "model", model_start_re, model_end_re)
    model_dict_bounds2 = locateDicts(f2, "model", model_start_re, model_end_re)

    if model_dict_bounds1 and model_dict_bounds2:

        (model_dict_start1, model_dict_end1) = model_dict_bounds1[0]
        (model_dict_start2, model_dict_end2) = model_dict_bounds2[0]

        # Compare the lines before the dictionaries (init, uuids, model order)
        if not compareLines(f1, f2, 0, 0, model_dict_start1 - 1):
            print("Error in compareLines")
            return False

        # Make sure we have the same number of spacecraft
        if len(model_dict_bounds1) != len(model_dict_bounds2):
            print("Error parsing model dictionaries in checkpoint files!")
            print(
                "  Left file has %d spacecraft and the right has %d!"
                % (len(model_dict_bounds1), len(model_dict_bounds2))
            )
            f1.close()
            f2.close()
            print("Error: Different number of vehicles")
            return False

        # Compare each of the spacecraft model dictionaries
        for i in range(0, len(model_dict_bounds1)):

            (model_dict_start1, model_dict_end1) = model_dict_bounds1[i]
            (model_dict_start2, model_dict_end2) = model_dict_bounds2[i]

            # Get the Dvar_Py model dictionaries
            str1 = getDictStr(f1, "model", model_dict_start1, model_dict_end1)
            str2 = getDictStr(f2, "model", model_dict_start2, model_dict_end2)

            # Get the model dictionary for file 1
            dict_re_old = re.compile(r"Dvar_Py.getDvar\([^\)]+\)\((.*)\)$")
            dict_re_new = re.compile(r"DshellObj.dvarContainer\(\).getDVar\([^\)]+\)\((.*)\)$")

            m1 = dict_re_old.match(str1)
            if not m1:
                m1 = dict_re_new.match(str1)
            if m1:
                try:
                    s = m1.group(1).replace(" nan,", "' nan',")
                    dict1 = eval(s)
                except:
                    print(
                        "Error in left file %s: Error parsing "
                        "model dictionary %d in checkpoint "
                        "file!" % (f1name, i + 1)
                    )
                    f1.close()
                    f2.close()
                    return False
            else:
                print(
                    "Error in left file %s: Not a checkpoint file! "
                    "(model dictionary %d not found around line %d)" % (f1name, i + 1, model_dict_start1)
                )
                f1.close()
                f2.close()
                return False

            # Get the model dictionary for file 2
            m2 = dict_re_old.match(str2)
            if not m2:
                m2 = dict_re_new.match(str2)
            if m2:
                try:
                    s = m2.group(1).replace(" nan,", "' nan',")
                    dict2 = eval(s)
                except:
                    print(
                        "Error in right file %s: Error parsing "
                        "model dictionary %d in checkpoint "
                        "file!" % (f2name, i + 1)
                    )
                    f1.close()
                    f2.close()
                    return False
            else:
                print(
                    "Error in right file %s: Not a checkpoint file! "
                    "(model dictionary %d not found around line %d)" % (f2name, i + 1, model_dict_start2)
                )
                f1.close()
                f2.close()
                return False

            # Compare the extracted model dictionaries
            if verbose:
                cmpDictsVerbose(dict1, dict2)
            else:
                if not cmpDicts(dict1, dict2):
                    f1.close()
                    f2.close()
                    return False
    else:
        # One or more of the files have no models
        if not model_dict_bounds1 and model_dict_bounds2:
            print("Error:  Left file '%s' has no models!" % f1name)
            return False
        if model_dict_bounds1 and not model_dict_bounds2:
            print("Error:  Right file '%s' has no models!" % f2name)
            return False

        # NOTE: If both files have no models, that is okay, continue

    # Get the Dvar_Py mbody dictionaries
    mbody_dict_bounds1 = locateDicts(f1, "mbody", mbody_start_re, mbody_end_re)
    mbody_dict_bounds2 = locateDicts(f2, "mbody", mbody_start_re, mbody_end_re)

    (mbody_dict_start1, mbody_dict_end1) = mbody_dict_bounds1[0]
    (mbody_dict_start2, mbody_dict_end2) = mbody_dict_bounds2[0]

    # If there are no model dictionaries, no need to compare the lines
    # between the model dictionaries and the mbody dictionary since it
    # only contains model order checks
    if model_dict_bounds1:
        # Compare lines between the model dictionaries and mbody dictionaries
        if not compareLines(
            f1,
            f2,
            model_dict_end1,
            model_dict_end2,
            (mbody_dict_start1 - model_dict_end1 - 1),
        ):
            print("Error comparing file contents between model and mbody dictionaries")
            return False

    # Make sure we have the same number of mbodys
    if len(mbody_dict_bounds1) != len(mbody_dict_bounds2):
        print("Error parsing mbody dictionaries in checkpoint files!")
        print("  Left file has %d mbodies and the right has %d!" % (len(mbody_dict_bounds1), len(mbody_dict_bounds2)))
        f1.close()
        f2.close()
        print("Error: Files have different number of mbodys")
        return False

    # Compare each pair of mbody dictionaries
    for i in range(0, len(mbody_dict_bounds1)):

        (mbody_dict_start1, mbody_dict_end1) = mbody_dict_bounds1[i]
        (mbody_dict_start2, mbody_dict_end2) = mbody_dict_bounds2[i]

        str1 = getDictStr(f1, "mbody", mbody_dict_start1, mbody_dict_end1)
        str2 = getDictStr(f2, "mbody", mbody_dict_start2, mbody_dict_end2)

        # Get the mbody dictionary for file 1
        dict_re = re.compile(r"DshellObj.mbody\(\).specNode\(\)\((.*)\)[;]*$")
        m1 = dict_re.match(str1)
        if m1:
            try:
                dict1 = eval(m1.group(1))
            except:
                print(
                    "Error in left file %s: Error parsing mbody dictionary " "%d in checkpoint file!" % (f1name, i + 1)
                )
                f1.close()
                f2.close()
                return False
        else:
            print(
                "Error in left file %s: Not a checkpoint file! "
                "(mbody dictionary not found around line %d)" % (f1name, mbody_dict_start1)
            )
            f1.close()
            f2.close()
            return False

        # Get the mbody dictionary for file 2
        m2 = dict_re.match(str2)
        if m2:
            try:
                dict2 = eval(m2.group(1))
            except:
                print(
                    "Error in right file %s: Error parsing mbody " "dictionary %d in checkpoint file!" % (f2name, i + 1)
                )
                f1.close()
                f2.close()
                return False
        else:
            print(
                "Error in right file %s: Not a checkpoint file! "
                "(mbody dictionary not found around line %d)" % (f2name, mbody_dict_start2)
            )
            f1.close()
            f2.close()
            return False

        # Compare the extracted dictionaries
        if verbose:
            cmpDictsVerbose(dict1, dict2)
        else:
            if not cmpDicts(dict1, dict2):
                f1.close()
                f2.close()
                return False

    # Now compare the lines after the dictionaries
    if not compareLines(
        f1,
        f2,
        mbody_dict_end1,
        mbody_dict_end2,
        countLines(f1) - mbody_dict_end1,
    ):
        print("Error comparing file contents after the dictionaries")
        return False

    # Wrap it up
    if not verbose:
        return True


def _stringIsIgnored(value):
    """Return True if string ignored based on IGNORE_STRING_PREFIXES."""
    for prefix in IGNORE_STRING_PREFIXES:
        if value.startswith(prefix):
            return True
    return False
