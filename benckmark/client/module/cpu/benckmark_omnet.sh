#!/bin/bash
########################################
# benchmark for CPU
#
########################################

curtdir=$(cd `dirname $0` && pwd)

. ${curtdir}/../../common/setenv.sh

logdir=${Logdir}/cpu
datadir="${Datadir}/cpu"
rm -fr ${logdir} ${datadir}
[ -d ${datadir} ] || mkdir -p ${datadir}
[ -d ${logdir} ] || mkdir -p ${logdir}

EXE=${DIDIVKIT}/arch/${ARCH}/kits/omnetpp
for ((i=0;i<NLCPU;i++))
do

	/bin/rm -rf ${logdir}/TMP_OmnetPP_${i}
	mkdir -p ${logdir}/TMP_OmnetPP_${i}
	cp -pr ${DIDIVKIT}/arch/${ARCH}/kits/omnetpp.ini ${logdir}/TMP_OmnetPP_${i}
done


TBEGIN=`date +%s`
for ((i=0;i<NLCPU;i++))
do
	cd ${logdir}/TMP_OmnetPP_${i}
	${DIDIVKIT}/arch/${ARCH}/bin/time -o time.${i}.out -f  %e\\t%P numactl -l -C $(expr $i + 0) $EXE > Temp_Output_omnetpp_${i} &
	cd ..
done
wait
TEND=`date +%s`

grep % ${logdir}/TMP_OmnetPP_*/time.*.out
res=$(echo $((TEND - TBEGIN)) | awk '{printf "%.03f\n", ($1 * 1.00) /"'$NLCPU'" }')
echo -e  "cpu\tcpu_omnetpp\t${res}" |tee ${datadir}/bk_cpu_omnetpp
