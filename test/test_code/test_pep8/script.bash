#!/bin/bash
#
# Check all Python files for coding style/correctness.

pep8 --max-line-length=120 --ignore=E731 --repeat ../../../python ../../../dtest
