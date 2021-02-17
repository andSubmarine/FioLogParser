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
    python ../src/fiohistogram.py -f "$f" -m simple -o "$name-hist.png" --outlier_cutoff 15 --bins 1000
    python ../src/fiohistogram.py -f "$f" -m simple -o "$name-hist-ylog.png" --outlier_cutoff 15 --bins 1000 --ylog
    python ../src/fiohistogram.py -f "$f" -m normal -o "$name-hist-normal.png" --outlier_cutoff 15 --bins 1000 -v
    python ../src/fiohistogram.py -f "$f" -m kernel -o "$name-hist-kernel.png" --outlier_cutoff 15 --bins 1000 -v
done