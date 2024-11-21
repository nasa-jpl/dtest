#!/bin/bash
#
# Check all Python files for bad syntax.

python -m compileall -q . ../../../python ../../../dtest
