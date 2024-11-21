#ifndef DTEST_GPU_MEM_H
#define DTEST_GPU_MEM_H

#include <cuda.h>
#include <cuda_runtime.h>

#include <nvml.h>

#include <iostream>

namespace Dtest {

    //! Return the total memory being used by the GPU
    inline size_t getGPUMemUsageCUDA()
    {
        size_t free, total;
        cudaMemGetInfo(&free, &total);
        return total - free;
    }

    //! Return the total memory available on the GPU
    inline size_t getGPUMemAvailableCUDA()
    {
        size_t free, total;
        cudaMemGetInfo(&free, &total);
        return free;
    }

    //! Return the total memory available on the GPU
    inline size_t getGPUMemTotalCUDA()
    {
        size_t free, total;
        cudaMemGetInfo(&free, &total);
        return total;
    }

    inline unsigned long long getGPUMemAvailable()
    {
        nvmlReturn_t result;
        result = nvmlInit();

        if (result != NVML_SUCCESS)
        {
            std::cerr << "Failed to initialize NVML: " << nvmlErrorString(result) << std::endl;
            return 0;
        }

        nvmlDevice_t device;
        result = nvmlDeviceGetHandleByIndex(0, &device);

        if (result != NVML_SUCCESS)
        {
            std::cerr << "Failed to get NVML device: " << nvmlErrorString(result) << std::endl;
            return 0;
        }

        nvmlMemory_t memory;

        result = nvmlDeviceGetMemoryInfo(device, &memory);
        if (result != NVML_SUCCESS)
        {
            std::cerr << "Failed to get NVML memory: " << nvmlErrorString(result) << std::endl;
            return 0;
        }

        return memory.free;
    }

    inline unsigned long long getGPUMemTotal()
    {
        nvmlReturn_t result;
        result = nvmlInit();

        if (result != NVML_SUCCESS)
        {
            std::cerr << "Failed to initialize NVML: " << nvmlErrorString(result) << std::endl;
            return 0;
        }

        nvmlDevice_t device;
        result = nvmlDeviceGetHandleByIndex(0, &device);

        if (result != NVML_SUCCESS)
        {
            std::cerr << "Failed to get NVML device: " << nvmlErrorString(result) << std::endl;
            return 0;
        }

        nvmlMemory_t memory;

        result = nvmlDeviceGetMemoryInfo(device, &memory);
        if (result != NVML_SUCCESS)
        {
            std::cerr << "Failed to get NVML memory: " << nvmlErrorString(result) << std::endl;
            return 0;
        }

        return memory.total;
    }

    inline unsigned long long getMemFromPIDandUtil(const unsigned int& pid, nvmlProcessDetailList_t& util)
    {

        for (unsigned int i = 0; i < util.numProcArrayEntries; i++)
        {
            if (pid == util.procArray[i].pid)
            {
                return util.procArray[i].usedGpuMemory;
            }
        }

        // std::cerr << "Failed to find process id " << pid <<std::endl;
        return 0;
    }

    inline unsigned long long getAndCheckRunningProcesses(const unsigned int& pid,
                                                          nvmlDevice_t& device,
                                                          nvmlProcessDetailList_t& processesUtilInfo)
    {
        nvmlReturn_t result;

        // get the processes info
        result = nvmlDeviceGetRunningProcessDetailList(device, &processesUtilInfo);

        if (result == NVML_SUCCESS)
        {
            //check the struct for requested PID
            return getMemFromPIDandUtil(pid, processesUtilInfo);
        }
        else if (result == NVML_ERROR_INSUFFICIENT_SIZE)
        {
            //try again with additional slots for info if we hadn't allocated enough before
            delete[] processesUtilInfo.procArray;
            processesUtilInfo.procArray = new nvmlProcessDetail_v1_t[processesUtilInfo.numProcArrayEntries];
            result = nvmlDeviceGetRunningProcessDetailList(device, &processesUtilInfo);
            if (result != NVML_SUCCESS)
            {
                std::cerr << "Failed to get NVML process info: " << nvmlErrorString(result) << std::endl;
                return 0;
            }
            return getMemFromPIDandUtil(pid, processesUtilInfo);
        }
        else
        {
            std::cerr << "Failed to get NVML process info: " << nvmlErrorString(result) << std::endl;
            return 0;
        }
    }


    /**
     * get GPU memory used. 
     * 
     * @param pid optional id of the process of interest. id of 0 gives total memory used
     */
    inline unsigned long long getGPUMemUsage(unsigned int pid = 0)
    {

        // although less efficient, we just do total-free from other functions.
        // Less efficient since both other functions initialize nvml, but
        // since it's super fast (~2.6 us), the cleanliness is more advantageous
        // than then increased time
        if (pid == 0)
            return getGPUMemTotal() - getGPUMemAvailable();

        // == Get the GPU memory used by a specific PID
        nvmlReturn_t result;

        //initialie nvml
        result = nvmlInit();
        if (result != NVML_SUCCESS)
        {
            std::cerr << "Failed to initialize NVML: " << nvmlErrorString(result) << std::endl;
            return 0;
        }

        // get the device, assuming we just want the first device on this host
        // if we have machines with multiple gpus, this needs to be updated
        nvmlDevice_t device;
        result = nvmlDeviceGetHandleByIndex(0, &device);
        if (result != NVML_SUCCESS)
        {
            std::cerr << "Failed to get NVML device: " << nvmlErrorString(result) << std::endl;
            return 0;
        }

        nvmlProcessDetailList_t processesUtilInfo;
        processesUtilInfo.numProcArrayEntries = 100; //max number of info structs we can get the first time around
        processesUtilInfo.procArray
            = new nvmlProcessDetail_v1_t[processesUtilInfo.numProcArrayEntries]; //allocate space for the info structs
        processesUtilInfo.version = nvmlProcessDetailList_v1;
        processesUtilInfo.mode = 1; //sue graphics mode (Compute/Graphics/MPSCompute) to compute mode

        //first checking graphics processes
        unsigned long long mem = getAndCheckRunningProcesses(pid, device, processesUtilInfo);
        if (mem > 0)
        {
            delete[] processesUtilInfo.procArray;
            return mem;
        }

        //doing a second check through compute processes if not in compute list
        //we need to reset and reallocate to ensure the previous check didn't clobber these, particularly numProcArrayEntries
        processesUtilInfo.numProcArrayEntries = 100; //max number of info structs we can get the first time around
        delete[] processesUtilInfo.procArray;
        processesUtilInfo.procArray
            = new nvmlProcessDetail_v1_t[processesUtilInfo.numProcArrayEntries]; //allocate space for the info structs
        processesUtilInfo.mode = 0; //switch to compute mode

        mem = getAndCheckRunningProcesses(pid, device, processesUtilInfo);
        delete[] processesUtilInfo.procArray;
        return mem;
    }

} // namespace Dtest

#endif // define DTEST_GPU_MEM_H
