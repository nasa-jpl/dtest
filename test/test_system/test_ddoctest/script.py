"""Ddoctest tests.

Ddoctest extends doctest by calling numpy.allclose so
numeric differences that fall under a specified tolerance
will pass.

To make existing script.py scripts work:
Add "from Dutils import Ddoctest" after "import doctest".

By default, Ddoctest passes the following parameters
to numpy.allclose:

relative error (stored in doctest.rtol) = 1.0000000000000001e-05
absolute error (stored in doctest.atol) = 1e-08


Change the tolerances for this test.

>>> from Dutils.Ddoctest import doctest
>>> doctest.rtol=1e-5; # relative error
>>> doctest.atol=1e-8; # absolute error


Scalars
-------

This test passes since relative error is under 1e-5

>>> x = 1.23
>>> x
1.230001

Lists
-----

allclose accepts vectors and matrices

>>> v = [[1.0, 2.0], [3.0, 4.0]]
>>> v
[[1.00001, 2], [2.999999, 4]]

The following fails since the difference is greater than the allowed tolerance.

>>> v
[[1.0001, 2], [2.999999, 4]]


numpy arrays
------------

>>> from numpy import array
>>> v = array([[1.0, 2.0], [3.0, 4.0]])

The expected value being a list of lists should match.

>>> v
[[1.00001, 2], [2.999999, 4]]

The expected value being an array should match.

>>> v
array([[1.00001, 2], [2.999999, 4]])

Dictionaries with arrays
------------------------

>>> d = {'a': array([[1.0, 2.0], [3.0, 4.0]]), 'b': [1.3, 2.4]}

>>> d
{'a': array([[1.0, 2.0], [3.0, 4.0]]), 'b': [1.3, 2.4]}



Dictionaries
------------

>>> d = {'a': 3.0, 'b': [1.3, 2.4]}

>>> d
{'a': 3.000003, 'b': [1.3, 2.400003]}

The following should fail since error is too large.

>>> d
{'a': 3.0003, 'b': [1.3, 2.400003]}

The following should fail since the expected value has the extra 'e' field.

>>> d
{'a': 3.000003, 'b': [1.3, 2.400003], 'e': 5}

The following should fail since the expected value has the missing 'a' field.

>>> d
{'b': [1.3, 2.400003]}


Dictionaries with strings
-------------------------

>>> d = {'a': 3.000003, 'b': [1.3, 2.400003], 'e': 5}
>>> d
{'a': 3.000003, 'b': [1.3, 2.400003], 'e': 5}

>>> d
{'b': [1.3, 2.400003], 'e': 5}



Changing the tolerance on the fly
---------------------------------

You can change the relative error on the fly.

>>> doctest.rtol = 1e-3
>>> x = 1.23
>>> x
1.2301

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

if __name__ == "__main__":
    from Dutils.Ddoctest import doctest

    doctest.testmod(optionflags=doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS)
