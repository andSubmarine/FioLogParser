#!/bin/sh
echo "Enter folder containing log files:"
read HOME_FOLDER    # /D/qd-1/nj8
echo "Enter log metric name (ex. bw, lat, iops):"
read METRIC
echo "Enter jobname (ex. seq-read):"
read JOBNAME
shopt -s nullglob
files=(${HOME_FOLDER}/*${JOBNAME}_${METRIC}.*.log)
for f in ${files[@]}
do 
    name="$(basename -s .log $f)"
    #python ../src/fiohistogram.py -f "$f" -m simple -o "$name-hist.png" --max 10000
    python ../src/fiohistogram.py -f "$f" -m simple -o "$name-hist-ylog.png" --ylog --max 10000
    #python ../src/fiohistogram.py -f "$f" -m normal -o "$name-hist-normal.png" -l 0.2 --xlog
    #python ../src/fiohistogram.py -f "$f" -m kernel -o "$name-hist-kernel.png" -l 0.2 --xlog
done