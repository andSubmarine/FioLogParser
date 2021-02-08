#!/bin/sh
echo "Enter folder containing log files:"
read HOME_FOLDER    # /D/qd-1/nj8
echo "Enter log metric name (ex. bw, lat, iops):"
read METRIC
echo "Enter jobname (ex. seq-read):"
read JOBNAME
shopt -s nullglob
files=(${HOME_FOLDER}/*${JOBNAME}_${METRIC}.*.log)
python ../src/fiologparser.py -m io_count -lt lat --every_nth 1000 --same_time -o "${JOBNAME}-iocount.png" -f "${files[@]}" -agg
for f in ${files[@]}
do 
    name="$(basename -s .log $f)"
    python ../src/fiologparser.py -m ios -lt lat --title "Latency for Samsung Pro 512G" -o "$name-ios-ylog.png" -f "$f" -ylog
done