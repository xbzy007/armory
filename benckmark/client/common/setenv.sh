#!/bin/bash 


Curtdir=$(cd `dirname $0` && pwd)
RootDir=${Curtdir%/client*}
###### LogParentDir 是数据产出路径，client.py 需要读取这个路径，client.py 需要保持一致
LogParentDir="/tmp/delivery"
export DIDIVKIT=${RootDir}/client/common
export ARCH=intel64
export LD_LIBRARY_PATH=${DIDIVKIT}/arch/${ARCH}/lib/:$LD_LIBRARY_PATH
export PATH=${DIDIVKIT}/arch/${ARCH}/bin:${DIDIVKIT}/arch/${ARCH}/kits:$PATH
export NLCPU=$(lscpu | grep -E "^CPU\(s\)" | awk '{print $2}')
export NNUMA=$(lscpu | grep -E "^NUMA node\(s\)" | awk '{print $3}')
export NHT=$(lscpu | grep -E "^Thread\(s\) per core" | awk '{print $4}')
export NSOCKETS=$(lscpu | grep -E "^Socket\(s\)" | awk '{print $2}')


# Haswell Broadwell: AVX2
# Skylake Xeon Silver 41xx: AVX2
# Skylake Xeon Gold 61xx: AVX512


export CPUMODEL="INTEL_AVX2"


lscpu | grep -E "^Model name" | grep -E "Intel\(R\)\ Xeon\(R\)\ Silver" > /dev/null 2>&1
if [ $? -eq 0 ]; then
        export CPUMODEL="INTEL_SKY_SILVER"
fi


lscpu | grep -E "^Model name" | grep -E "Intel\(R\)\ Xeon\(R\)\ Gold" > /dev/null 2>&1
if [ $? -eq 0 ]; then
        export CPUMODEL="INTEL_SKY_GOLD"
fi


initworkdir()
{
        Logdir=${LogParentDir}/logs
        Datadir=${LogParentDir}/data
        mkdir -p $Logdir $Datadir
}

initworkdir
#env

