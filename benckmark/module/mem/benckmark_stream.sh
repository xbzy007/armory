#!/bin/bash
#########################
# benchmark memory
#
#########################
curtdir=$(cd `dirname $0` && pwd)

. ${curtdir}/../../common/setenv.sh


EXE=${DIDIVKIT}/arch/${ARCH}/kits/stream.icc17.avx2
NTOTAL=3

logdir=${Logdir}/memory
datadir=${Datadir}/memory
rm -fr ${logdir} ${datadir}
[ -d ${datadir} ] || mkdir -p ${datadir}
[ -d ${logdir} ] || mkdir -p ${logdir}

### 2 sockets only

for ((i=0;i<NTOTAL;i++))
do
	OMP_NUM_THREADS=$(($NLCPU / $NSOCKETS / $NHT)) KMP_AFFINITY='verbose,scatter,granularity=fine' numactl -m0 -N1 $EXE  &> ${logdir}/TMP_STREAM_CROSS_${i}_1.txt
	OMP_NUM_THREADS=$(($NLCPU / $NSOCKETS / $NHT)) KMP_AFFINITY='verbose,scatter,granularity=fine' numactl -m1 -N0 $EXE  &> ${logdir}/TMP_STREAM_CROSS_${i}_2.txt
	OMP_NUM_THREADS=$(($NLCPU / $NSOCKETS / $NHT)) KMP_AFFINITY='verbose,scatter,granularity=fine' numactl -m0 -N0 $EXE  &> ${logdir}/TMP_STREAM_LOCAL_${i}_1.txt
	OMP_NUM_THREADS=$(($NLCPU / $NSOCKETS / $NHT)) KMP_AFFINITY='verbose,scatter,granularity=fine' numactl -m1 -N1 $EXE  &> ${logdir}/TMP_STREAM_LOCAL_${i}_2.txt
done


res=$(grep Triad ${logdir}/TMP_STREAM_CROSS*.txt | awk 'BEGIN {AVG=0.0; SUM=0.0;} {SUM += $2} END {AVG = SUM / NR; print AVG}')
if [ -z "$res" ];then
    res=-1
fi
echo -e "memory\tSTREAM_CROSS\t${res}" | tee -a ${datadir}/bk_stream_cross

res=$(grep Triad ${logdir}/TMP_STREAM_LOCAL*.txt | awk 'BEGIN {AVG=0.0; SUM=0.0;} {SUM += $2} END {AVG = SUM / NR; print AVG}')
if [ -z "$res" ];then
    res=-1
fi
echo -e "memory\tSTREAM_LOCAL\t${res}" | tee -a ${datadir}/bk_stream_local
