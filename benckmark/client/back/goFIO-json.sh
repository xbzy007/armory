#!/bin/bash

. ./setenv.sh



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
#size=${4}
size="1M"

EOF
}


preconf()
{
#1.81TB BUG
#lsscsi -s | grep B$ | sed 's/.*\ \//\//g;s/GB//g;s/TB/000/g' | awk '{if($2 > 256) print $2,$1}' | sort -n | while read line; do echo $line; done
diskinfo=$(lsscsi -s | grep B$ | awk 'BEGIN{OFS="--"}{print $(NF -1),$NF}')
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


formatdatatojson()
{   
    local diskinfo=$(lsscsi -s | grep B$ | awk '{print $(NF -1)}')
    local diskinfo_arr=(${diskinfo// / })
    local outfile="$1"
    local datatype="$2"
    printf "{\n"
    printf "\t\"${datatype}\":[\n"
    for ((i=0;i<${#diskinfo_arr[@]};i++))
    do  
        if [ "${diskinfo_arr[i]}" == "/dev/sda" ];then
          # echo "skip ${diskinfo_arr[i]}"
           continue
        fi
        var=$(grep "${diskinfo_arr[i]}" -A 1 ${outfile} |grep -Eo 'bw=[0-9]+'|awk '{print }'|awk -F'=' '{print $2}')
        printf '\t\t{\n'
        num=$(echo $((${#diskinfo_arr[@]}-1)))
        if [ "$i" == ${num} ];
        then    
                printf "\t\t\t\"${diskinfo_arr[$i]}\":\"${var}\"}\n"
        else    
                printf "\t\t\t\"${diskinfo_arr[$i]}\":\"${var}\"},\n"
        fi
   done
   printf "\t]\n"
   printf "}\n"
}



FNAME="fio_ini.ini"

IODEPTH=32
METHOD=read
BS=1M
RUNTIME=3600
#RUNTIME=60
test -f $FNAME && rm -f $FNAME 
genHead
preconf

RES_LOG="./logs/FIO_eta_seq_r1M.log"
fio --eta=always $FNAME > $RES_LOG
#grep aggrb $RES_LOG | sed 's/\,//g;s/=/ /g;s/\/s//g'| awk '{print $5}' | numfmt --from=iec --suffix=B | sed -e 's/B//' | awk '{printf "%.02f\n", $1/(1024*1024)}'
formatdatatojson ${RES_LOG} Seqr1M


#sed -i "s/bs\=${BS}/bs\=4k/g; s/rw\=${METHOD}/rw\=randread/g; s/iodepth\=${IODEPTH}/iodepth\=128/g" $FNAME
#cat $FNAME

IODEPTH=32
METHOD=read
BS=1M
RUNTIME=3600
#RUNTIME=60
test -f $FNAME && rm -f $FNAME
genHead
preconf

RES_LOG="./logs/FIO_eta_rand_r4k.log"
fio --eta=always $FNAME > $RES_LOG
#grep aggrb $RES_LOG | sed 's/\,//g;s/=/ /g;s/\/s//g'| awk '{print $5}' | numfmt --from=iec --suffix=B | sed -e 's/B//' | awk '{printf "%.02f\n", $1/(1024*1024)}'
formatdatatojson ${RES_LOG} Randr4K
