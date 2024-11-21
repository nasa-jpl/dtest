"""Returns file meta data via magic."""

from __future__ import division
from __future__ import print_function

from __future__ import absolute_import

import subprocess


def magicString(filename):
    """Return what libmagic thinks the filetype is."""
    process = subprocess.Popen(["file", "--dereference", filename], stdout=subprocess.PIPE)
    return process.communicate()[0].decode("utf-8").strip()
