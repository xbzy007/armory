. ./setenv.sh

DISCARD=60
HEAD=5
TAIL=5

FILE=$1
TMPFILE1=/tmp/f


	NLINE=$(grep eta $FILE | wc -l)
	echo $FILE | grep -E "_r[0-9]" > /dev/null 2>&1
	if [ $? -eq 0 ]; then
		grep eta $FILE | tail -n $((NLINE - DISCARD)) | awk '{print $7}' | sed -e 's/\[//' | awk -F\/ '{print $1}' | numfmt --from=iec --suffix=B | sed -e 's/B//' | awk '{printf "%.02f\n", $1/(1024*1024)}' > ${TMPFILE1}
	else
		grep eta $FILE | tail -n $((NLINE - DISCARD)) | awk '{print $7}' | sed -e 's/\[//' | awk -F\/ '{print $2}' | numfmt --from=iec --suffix=B | sed -e 's/B//' | awk '{printf "%.02f\n", $1/(1024*1024)}' > ${TMPFILE1}
	fi

AVG=$(grep aggrb $FILE | sed 's/\,//g;s/=/ /g;s/\/s//g'| awk '{print $5}' | numfmt --from=iec --suffix=B | sed -e 's/B//' | awk '{printf "%.02f\n", $1/(1024*1024)}')
MIN=$(cat $TMPFILE1 | sort -n | head -n $HEAD | awk '{sum+=$1} END {print sum/NR}')
MAX=$(cat $TMPFILE1 | sort -n | tail -n $TAIL | awk '{sum+=$1} END {print sum/NR}')
AVG2=$(cat $TMPFILE1 | awk '{sum+=$1} END {print sum/NR}')

echo $AVG $MIN $MAX $AVG2

