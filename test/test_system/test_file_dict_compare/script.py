"""Test the cmpDictsInFiles() function.

>>> from Dutils import DCompareUtils
>>> from Dutils.DCompareUtils import *

>>> cmpDictsInFiles('file1.txt', 'file2.txt', '<START>', '<END>')
True

>>> cmpDictsInFiles('file1.txt', 'file3.txt', '<START>', '<END>')
False

>>> cmpDictsInFiles('file1.txt', 'file4.txt', '<START>', '<END>')
True

>>> cmpDictsInFiles('file1.txt', 'filebad.txt', '<START>', '<END>')
Traceback (most recent call last):
...
ValueError: End of dictonary in file 'filebad.txt' not located by line 10


Test changing tolerances

>>> cmpDictsInFiles('file1.txt', 'file5.txt', '<START>', '<END>')
False

>>> cmpDictsInFiles('file1.txt', 'file5.txt', '<START>', '<END>', new_rel_eps=1.0e-8)
True

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

if __name__ == "__main__":
    import doctest
    import sys

    if doctest.testmod(optionflags=doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS)[0]:
        sys.exit(1)
