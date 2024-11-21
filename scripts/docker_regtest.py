# Utility to run all regtests.
# This is intended to be used on docker images where `make regtest` does not work.
# Run this script in the src/ directory.
#
# May need to set LD_LIBRARY_PATH in docker first
# export LD_LIBRARY_PATH=$COMPASS_FOSS_PATH/lib
import sys, os, glob

# Exclude tags for DsendsCompassBasePkg
tags = "graphics,Arkode_Py,AeroMarsGRAMModels,AeroMERModels,AeroM01LanderModels,AeroMSLModels,AspireControlModels,dartspp,dcraft,DspaceOgre,EDLNavFilterModels,GravityModelData,MAVModels,NdartsConstraints,NdartsContact,NdartsFlex,NESCFlex,optix,PowerModels,pycraft,RoverDynModels,VCDModels,bullet,cheetah,gdal,gtest,gts,imagemagick,codechecking,codestyle,jpl_terrains,spice_file,lcm,pandas,pygame,ros,jplv,python2,gdal,kmlengine,pygtk,click,sympy,assimp,embree,cgal,submesh,IPython,pango,matlab,dca"

dirs = glob.glob("*/")
for f in dirs:
    s = "cd " + f + "; srun dtest --exclude-tags=%s; cd .." % tags
    print("=============================")
    print(s)
    sys.stdout.flush()
    os.system(s)
print("==== DONE =====")
