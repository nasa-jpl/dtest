#!/usr/bin/env python
"""Setup for dtest."""
from __future__ import division
from __future__ import print_function

from __future__ import absolute_import

from distutils import core
import glob

core.setup(
    name="dtest",
    packages=["Dtest"],
    package_dir={"Dtest": "python"},
    scripts=["dtest"] + glob.glob("./scripts/*"),
)
