.. index::
   single: Mail Generation Regtest
   single: Regtest; Mail Generation


test_genRegtestMail
====================

This test uses the genRegtestMail command to process a fixed execution data file
(the output of a 'dtest' run) to generate mail files with regression testing information.
This test configuration uses several command line options to verify correct processing of
field values.

The DTESTDEFS file for this test is defined as:

::

  # Parameterized commands executed as part of this test
  [RUN]

   test1 = genRegtestMail --dataFile test_regtest.data --title "Test Default Module Owner" --output mail1.out
   test2 = genRegtestMail --dataFile test_regtest.data --title "Test String Eval Module Owner" --output mail2.out --moduleOwner="{'Dtest' : 'George'}"
   test3 = genRegtestMail --dataFile test_regtest.data --title "Test File Eval Module Owner" --output mail3.out --moduleOwner='mod_own.py'
   test4 = genRegtestMail --dataFile test_regtest.data --title "Test HTML Output" --html --output mail4.html.out --moduleOwner="{'Dtest' : 'John'}"
