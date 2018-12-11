#!/bin/bash
####################################################
# require seq expr
# benchmark for CPU Scientific Computing
#
####################################################

curtdir=$(cd `dirname $0` && pwd)

######. ${curtdir}/../../common/setenv.sh


logdir=${Logdir}/cpu
datadir="${Datadir}/cpu"
rm -fr ${logdir} ${datadir}
[ -d ${datadir} ] || mkdir -p ${datadir}
[ -d ${logdir} ] || mkdir -p ${logdir}
EXE=${DIDIVKIT}/arch/${ARCH}/kits/sjeng
for ((i=0;i<NLCPU;i++))
do
        /bin/rm -rf ${logdir}/TMP_Sjeng_${i}
        mkdir ${logdir}/TMP_Sjeng_${i}
        cp -pr ${DIDIVKIT}/arch/${ARCH}/kits/sjeng.ini ${logdir}/TMP_Sjeng_${i}
done


TBEGIN=`date +%s`
for ((i=0;i<NLCPU;i++))
do
        cd ${logdir}/TMP_Sjeng_${i}
        ${DIDIVKIT}/arch/${ARCH}/bin/time -o time.${i}.out -f  %e\\t%P numactl -l -C $(expr $i + 0) $EXE sjeng.ini > Temp_Output_sjeng_${i} &
done
wait
TEND=`date +%s`

grep '%' ${logdir}/TMP_Sjeng_*/time.*.out
res=$(echo $((TEND - TBEGIN)) | awk '{printf "%.03f\n", ($1 * 1.00) /"'$NLCPU'" }')
echo -e "cpu\tcpu_sjeng\t${res}" |tee ${datadir}/bk_cpu_sjeng
