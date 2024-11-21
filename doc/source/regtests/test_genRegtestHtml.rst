.. index::
   single: HTML Generation Regtest
   single: Regtest; HTML Generation


test_genRegtestHtml
===================

This test uses the genRegtestHtml command to process a fixed execution data file
(the output of a 'dtest' run) to generate an HTML formatted status page.

The DTESTDEFS file for this test is defined as:

::

  # Comparison command with the expected differences specified as a regular expression input file
  CMP = cmp.prg 0 ROOTDIR/test_genRegtestHtml/cmpregexp.lst,  cmp.prg 1 ROOTDIR/test_genRegtestHtml/cmpregexp.lst

  # Parameterized command to be executed as part of this test
  [RUN]

   test1 = genRegtestHtml --dataFile test_regtest.data --title "Test Output" --output html.out
