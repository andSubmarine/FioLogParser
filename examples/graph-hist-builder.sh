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
    python ../src/fiohistogram.py -f "$f" -m simple -o "$name-hist.png" --bins 100
    python ../src/fiohistogram.py -f "$f" -m simple -o "$name-hist-ylog.png" --bins 100 --ylog
    python ../src/fiohistogram.py -f "$f" -m simple -o "$name-cdf.png" --bins 100 -hm cdf
    python ../src/fiohistogram.py -f "$f" -m normal -o "$name-hist-normal.png" --bins 100 -v
    # warning enabling the next line will slow down execution considerably due to model training - use limit and/or cutoff to reduce dataset
    # python ../src/fiohistogram.py -f "$f" -m kernel -o "$name-hist-kernel.png" --bins 100 -v -c 20 -ll 0.1 -kbw 0.5 
done