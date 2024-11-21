import os
from Dtest.regtest.processRegtestData import writeFilesToHDF5

writeFilesToHDF5("test.h5", [os.path.abspath("regtest.data-2024-04-22-06_05")], append=False)
