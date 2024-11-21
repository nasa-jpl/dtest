"""

>>> import filecmp

>>> from Dutils import DCompareUtils
>>> from Dutils.DCompareUtils import *

Floats less than this will be treated as zero during comparisons.

>>> DCompareUtils.abseps
1e-12

The threshold tolerance on the relative error.

>>> DCompareUtils.releps = 1e-7


>>> d1 = { 'v1' : 1.0,
...        'v2' : 1.0000000000001,
...        'v3' : 'test',
...        'v4' : { 'v1' : 23,
...                 'v2' : { 1 : 23.5, 'a' : 5.6 },
...                 'v3' : 'soup' }
...      }

>>> d2 = { 'v1' : 1,  # <-- DIFF, but value the same: hash(1) == hash(1.0)
...        'v2' : 1.0000000000001,
...        'v3' : 'test',
...        'v4' : { 'v1' : 23,
...                 'v2' : { 1 : 23.5, 'a' : 5.6 },
...                 'v3' : 'soup' }
...      }


>>> d3 = { 'v1' : 1.0,
...        'v2' : 1.0000000000001,
...        'v3' : 'test',
...        'v4' : { 'v1' : 23.1, # <-- DIFF
...                 'v2' : { 1 : 23.5, 'a' : 5.6 },
...                 'v3' : 'soup' }
...      }


>>> d4 = { 'v1' : 1.0,
...        'v2' : 1,     # <-- EPS DIFF (abseps = 1.0e-12)
...        'v3' : 'test',
...        'v4' : { 'v1' : 23,
...                 'v2' : { 1 : 23.5, 'a' : 5.6 },
...                 'v3' : 'soup' }
...      }


>>> d1 == d2
True

>>> cmpDicts(d1, d2)
True


>>> d1 == d3
False

>>> cmpDicts(d1, d3)
False

Now update d3 so that the difference falls within the relative
tolerance. Even though the dictionaries are different, the comparison
routine reports them as agreeing.

>>> d1 == d3
False

>>> d3['v4']['v1'] = 23.0000004

>>> cmpDicts(d1, d3)
True

>>> cmpDictsVerbose(d1, d3)



>>> d1 == d4
False

>>> cmpDicts(d1, d4)
True


Now change the keys in d4. The comparison should fail now.

>>> del d4['v3']
>>> d4['v4']['new'] = 5

>>> cmpDicts(d1, d4)
False


>>> cmpDictsVerbose(d1, d4)
Extra keys on Left at dict[] ==>  ['v3']
Extra keys on Right at dict[v4] ==>: ['new']


Now test some model files
-------------------------

>>> filecmp.cmp('model.out', 'model.out')
True

>>> cmpModelFiles('model.out', 'model.out', False)
True


model.out2 has a very small difference in one floating point number (1e-15)

>>> filecmp.cmp('model.out', 'model.out2')
False

>>> cmpModelFiles('model.out', 'model.out2', False)
True


model.out3 has a small but significant difference in one floating point number (1e-6)

>>> filecmp.cmp('model.out', 'model.out3')
False

>>> cmpModelFiles('model.out', 'model.out3', False)
False

Now get diffs.

>>> cmpModelFiles('model.out', 'model.out3', True)
* ASSEMBLY.Global.ASSEMBLY.sun_angle.Flow MODELS.sun_angle.PARAMS.longitude: -2.06088304 vs -2.060882 rel= 5.04638050637e-07


Test some checkpoint files
--------------------------

>>> cmpCheckpointFiles('checkpoint-000', 'checkpoint-000', False)
True

checkpoint-000-mod has a couple of small, insignificant differences

>>> cmpCheckpointFiles('checkpoint-000', 'checkpoint-000-mod', False)
True


checkpoint-000-mod2 has a couple of small but significant differences

>>> cmpCheckpointFiles('checkpoint-000', 'checkpoint-000-mod2', False)
False


Now get the diffs.

>>> cmpCheckpointFiles('checkpoint-000', 'checkpoint-000-mod2', True)
* R8.R8Hdw.chassis.chassisLeft.param.Bodies.WheelCenterLeft.cmInertia: 0.0021 vs 0.00209999 rel= 4.76190476188e-06

checkpoint-000-mod3 has a difference before the dictionary

>>> cmpCheckpointFiles('checkpoint-000', 'checkpoint-000-mod3', False)
Error in compareLines
False

Now get the diffs.

>>> cmpCheckpointFiles('checkpoint-000', 'checkpoint-000-mod3', True)
Difference at line:
  15 <  assert instanceFromUuidInt(164).name() == 'BogeyLeft_encoder'
  15 >  assert instanceFromUuidInt(164).name() == 'BogeyLeft_encoderX'

checkpoint-000-mod4 has a difference after the dictionary

>>> cmpCheckpointFiles('checkpoint-000', 'checkpoint-000-mod4', False)
Error comparing file contents after the dictionaries
False

Now get the diffs.

>>> cmpCheckpointFiles('checkpoint-000', 'checkpoint-000-mod4', True)
Difference at line:
5008 <  DshellSignal.signalObjFromUuid(32).time(-1)  ## .Spacecraft.Roams.R8.R8Hdw.chassis.signals.bogeyRight_angle
5008 >  DshellSignal.signalObjFromUuid(32).time(1)  ## .Spacecraft.Roams.R8.R8Hdw.chassis.signals.bogeyRight_angle

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

if __name__ == "__main__":
    import doctest
    import sys

    if doctest.testmod(optionflags=doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS)[0]:
        sys.exit(1)
