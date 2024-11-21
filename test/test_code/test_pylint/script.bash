#!/bin/bash
#
# Check all Python files for coding style/correctness.

# Only load the most basic site packages (avoid SWIG-related packages)
export PYTHONPATH="/home/dartsfn/pkgs/$YAM_TARGET/lib/python2.7/site-packages"

TEMPLATE="--msg-template='{msg_id}:{line:3d}:{obj}: {msg}'"

pylint \
    --rcfile="../../../pylintrc" \
    --output-format=text "$TEMPLATE" \
    --init-import=no \
    --dummy-variables-rgx='^_+$' \
    --disable=too-many-branches \
    --disable=too-many-locals \
    --disable=W0702,E0401,R1714,R1718 \
    ../../../python/Test*.py \
    ../../../dtest
