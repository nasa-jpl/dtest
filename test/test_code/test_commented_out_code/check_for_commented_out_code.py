#!/usr/bin/env python
"""Check all Python files for commented out code."""
from __future__ import division

from __future__ import absolute_import
from __future__ import print_function

import sys


def containsCode(input_string):
    code_examples = [
        r"^\s*#*\s*print\s*[\(\'\"].*$",
        r"^\s*#*\s*def\s+[a-zA-Z0-9_]+\(.*$",
        r"^\s*#*\s*class\s+[a-zA-Z0-9_]+.*:\s*$",
        r"^\s*#*\s*if\s+[^:]+ *: *$",
    ]

    for line in input_string.split("\n"):
        for example in code_examples:
            import re

            if re.match(example, line):
                return True
    return False


def main():
    import argparse

    parser = argparse.ArgumentParser("check_for_commented_out_code")
    parser.add_argument("filenames", nargs="*")
    args = parser.parse_args()

    if not args.filenames:
        sys.stderr.write("Requires filename arguments.\n")
        return 1

    failed = False
    for filename in args.filenames:
        file_object = open(filename)
        import tokenize

        g = tokenize.generate_tokens(file_object.readline)
        for token_type, token_value, (start_row, _), _, _ in g:
            if token_type == tokenize.COMMENT:
                # If there is a print statement/function in the comment it
                # probably is commented out code.
                if containsCode(token_value):
                    sys.stderr.write(
                        "Commented out code starting with "
                        '"{first_few}" found at {filename}:{line_number}\n'.format(
                            first_few=token_value[: min(len(token_value), 20)],
                            filename=filename,
                            line_number=start_row,
                        )
                    )
                    failed = True

    if failed:
        sys.stderr.write("Commented out code was found. Delete the code " "(make use of revision control).\n")
        return 2
    else:
        return 0


if __name__ == "__main__":
    sys.exit(main())
