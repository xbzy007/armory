#!/bin/bash
#########################
# benchmark disk
#
#########################

curtdir=$(cd `dirname $0` && pwd)

source ${curtdir}/../../common/setenv.sh 

genHead() {

cat << EOF > $FNAME

[global]

ioengine=libaio
iodepth=${IODEPTH}
rw=${METHOD}
#rwmixread=0
bs=${BS}
time_based
runtime=${RUNTIME}
#loops=10
direct=1
#size=${SIZE}

EOF
}


genTask() {

local taskname="$1"
cat << EOF >> $FNAME

[${taskname}]
cpus_allowed=${2}
filename=${3}
offset=0g
size=${4}

EOF
}


preconf()
{
    diskinfo=$(lsscsi -s |grep -v sda | grep B$ | awk 'BEGIN{OFS="--"}{print $(NF -1),$NF}')
    #echo $diskinfo
    diskinfo_arr=(${diskinfo// / })
    #echo $diskinfo_arr
    i=0
    for ((j=0;j<${#diskinfo_arr[@]};j++))
    do 
        echo ${diskinfo_arr[$j]}
        DEV=$(echo ${diskinfo_arr[$j]} | awk -F'--' '{print $1}')
        SizeGiB=$(echo ${diskinfo_arr[$j]} | awk -F'--' '{print $2}' | numfmt --from=si --suffix=B | sed -e 's/B//' | awk '{printf "%.00f\n", $1/1024/1024/1024}' )
        if [ $SizeGiB -lt 256 ]; then
                #echo "Skip $DEV $SizeGiB GiB"
                continue;
        fi
        let i+=1
        genTask $DEV $((i % NLCPU)) ${DEV} ${SizeGiB}G 
        #echo $DEV $SizeGiB
    done

}


formatdatatofile()
{   
    local diskinfo=$(lsscsi -s |grep -vi '/dev/sda' | grep B$ | awk '{print $(NF -1)}')
    local diskinfo_arr=(${diskinfo// / })
    local outfile="$1"
    local datatype="$2"
    local bwfile="${datatype}_bw"
    local iopsfile="${datatype}_iops"
    # 定义字典存放json中磁盘位置
    [ -f ${outfile} ] ||  { echo "${outfile} not found"; exit 2; }
    declare -A dictdisk 
    length=$(cat ${outfile} | python -c "import sys, json; datadic=(json.load(sys.stdin))['jobs']; print len(datadic)")
    for ((i=0;i<length;i++))
    do 
        devname=$(cat ${outfile}| python -c "import sys, json; print(json.load(sys.stdin))['jobs'][$i]['jobname']")
        dictdisk["${devname}"]=${i}
    done
    ### 清理文件
    [ -f ${datadir}/${bwfile} ] && rm -f ${datadir}/${bwfile}
    [ -f ${datadir}/${iopsfile} ] && rm -f ${datadir}/${iopsfile}
    
    #### 从测试输出的文件中获取 每个磁盘的字典的位置
    for ((i=0;i<${#diskinfo_arr[@]};i++))
    do  
        thedev="${diskinfo_arr[i]}"
        if [ "${thedev}" == "/dev/sda" ];then
           continue
        fi
        tags=${dictdisk["${thedev}"]}
        bw_read=$(cat ${outfile} | python -c "import sys, json; print(json.load(sys.stdin))['jobs'][$tags]['read']['bw']")
        bw_write=$(cat ${outfile} | python -c "import sys, json; print(json.load(sys.stdin))['jobs'][$tags]['write']['bw']")
        iops_read=$(cat ${outfile} | python -c "import sys, json; print(json.load(sys.stdin))['jobs'][$tags]['read']['iops']")
        iops_write=$(cat ${outfile} | python -c "import sys, json; print(json.load(sys.stdin))['jobs'][$tags]['write']['iops']")
        
        bw=$(awk -v bw_read=${bw_read} -v bw_write=${bw_write} 'BEGIN{printf "%.2f\n",bw_read+bw_write}')
        iops=$(awk -v iops_read=${iops_read} -v iops_write=${iops_write} 'BEGIN{printf "%.2f\n",iops_read + iops_write}')
       
        if [ -z "${bw}" ];then
            bw=0
        elif [ -z "${iops}" ];then
            iops=-1
        fi
        echo -e "${diskinfo_arr[i]}\t${bwfile}\t${bw}"| tee -a  ${datadir}/${bwfile}
        echo -e "${diskinfo_arr[i]}\t${iopsfile}\t${iops}"| tee -a  ${datadir}/${iopsfile}
   done
}



main()
{

    if [ $# -ne 3 ];then
        echo "Usage: sh $0 arg1[ METHOD ]  arg2[ BS ] arg3[ runtime ]"
        exit 1
    fi
    
    
    datadir=${Datadir}/disk
    logdir=${Logdir}/disk
    info="DISKINFO"
    [ -f ${datadir}/${info} ] && rm -f ${datadir}/${info}
    [ -d ${datadir} ] || mkdir -p ${datadir}
    [ -d ${logdir} ] || mkdir -p ${logdir}
    
    FNAME="fio_ini.ini"
    
    
    METHOD="$1"
    BS="$2"
    RUNTIME="$3"
    
    RES_LOG="${logdir}/FIO_${METHOD}_${BS}.log"
    case $METHOD in 
        # 顺序度
        read)
            IODEPTH=32
            ;;
        #随机读
        randread)
            IODEPTH=128     
            ;;
        # 顺序写
        write)
            IODEPTH=32
            ;;
        # 随机写
        randwrite)
            IODEPTH=32
            ;;
        # 混合随机读写
        randrw) 
            IODEPTH=32
            ;;
        *)
            echo -e "METHOD : read/randread/write/randwrite/randrw \
                 BS : 4K/1M/512K"
            exit 2
    esac
    
    case $BS in
        4K)
            ;;
        1M)
            ;;
        512K)
            ;;
        *)
            echo -e "METHOD : read/randread/write/randwrite/randrw \
                BS : 4K/1M/512K"
            exit 2
    esac
    
    
    test -f $FNAME && rm -f $FNAME
    genHead
    preconf
    fio --eta=always ${FNAME} --output=${RES_LOG} --output-format=json
    formatdatatofile ${RES_LOG} bk_${METHOD}_${BS}
}

main $@
