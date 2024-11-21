#ifndef DTEST_GPU_MEM_I
#define DTEST_GPU_MEM_I

%define DOCSTRING
"The `DtestGpuMem` module provides functions to query GPU memory."
%enddef

// use of the moduleimport command removes instance new_instancemethod
// definition from the _Py.py file breaking split import mode
#if SWIG_VERSION <= 0x030012
    %module(package="Dshell",docstring=DOCSTRING) DtestGpuMem_Py
#else
    %module(package="Dshell",docstring=DOCSTRING, moduleimport="import $module") DtestGpuMem_Py
#endif

%feature("autodoc", "1");
%feature("python:annotations", "c");
%ignore "Dtest::storage_lock";
%ignore "Dtest::_dtest_allocated_storage";

%{
    #include "gpu_mem.cc"
%}

%ignore "Dtest::getMemFromPIDandUtil";
%ignore "Dtest::getAndCheckRunningProcesses";


%include "gpu_mem.cc"

#endif // DTEST_GPU_MEM_I
