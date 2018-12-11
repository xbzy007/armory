#!/bin/bash
################################
# benchmark for CPU
# unit  GFLOPS
################################

curtdir=$(cd `dirname $0` && pwd)

#######. ${curtdir}/../../common/setenv.sh

logdir=${Logdir}/cpu
[ -d ${logdir} ] || mkdir -p ${logdir}
datadir="${Datadir}/cpu"
[ -d ${datadir} ] || mkdir -p ${datadir}

cp -pr ${DIDIVKIT}/arch/${ARCH}/kits/HPL.dat ${logdir}


cd ${logdir} && ${DIDIVKIT}/arch/${ARCH}/kits/xhpl_intel64_static &> ${logdir}/HPL.out

res=$(grep -E ^WC00C2R2 ${logdir}/HPL.out |tail -1| awk '{printf "%.03f\n", $7}')
echo -e "cpu\tdefault\t${res}" | tee ${datadir}/bk_cpu_mplinpack
