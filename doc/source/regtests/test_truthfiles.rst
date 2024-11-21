.. index::
   single: Truth Files Regtest
   single: Regtest; Truth Files


test_truthfiles
====================

This test evalutes the use of alternative "truth" file suffixes (i.e., file extensions
other than the ``.orig`` default).  A short DTESTDEFS file for this test is defined as
(all other values are inherited from the DTESTDEFS in the parent directory):

::

   # Dtest will look for comparison files ending in .truth first, and use .orig as a fallback
   TRUTHSUFFIX = truth
