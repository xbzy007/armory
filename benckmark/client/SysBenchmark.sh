#!/bin/bash
curtdir=$(cd `dirname $0` && pwd)

. ${curtdir}/common/setenv.sh


sysinfolog="system_info"

logfile="${curtdir}/benchmark.log"
modulefile="${curtdir}/module"

{
    uname -a
    cpupower frequency-info
    cpupower idle-info
    cpupower idle-set -D 10
    cpupower frequency-set -g performance
    cpupower frequency-info
    cpupower idle-info
    lscpu
    lsscsi -s
    ls -l /dev/disk/by-id/
    lspci -vt
    dmidecode

}&>> ${curtdir}/$sysinfolog

helpinfo()
{
    echo "Usage:sh $0 memory/cpu/disk"
    exit 1
}

if [ $# -ne 1 ];then
    helpinfo
fi

action="$1"
case $action in
    memory)
    ##### 内存带宽
    sh ${modulefile}/mem/benckmark_stream.sh &>> $logfile && sleep 10
    ;;

    cpu)
    ####### 科学计算
    #sh ${modulefile}/goOmnet.sh &>> $logfile && sleep 30
    sh ${modulefile}/cpu/benckmark_sjeng.sh &>> $logfile
    wait
    #浮点计算
    sh ${modulefile}/cpu/benckmark_mplinpack.sh &>> $logfile && sleep 20
    ;;

    disk)
    #磁盘带宽
    runtime=60
    sleep_interval=20
    FioType=('read' 'randread' 'write' 'randwrite')
    BsType=('4K' '1M')

    for ((i=0;i<${#FioType[@]};i++))
    do
        for ((j=0;j<${#BsType[@]};j++))
        do
            sh ${modulefile}/disk/benckmark_fio.sh ${FioType[i]} ${BsType[j]} ${runtime} &>> $logfile
            sleep ${sleep_interval}
        done
    done
    #
    sh ${modulefile}/disk/benckmark_fio.sh randrw "512K" ${runtime}  &>> $logfile
    ;;

    *)
    helpinfo
    ;;

esac
