#!/bin/sh
# Given a folder and arguments to find log files, the graph-hist-builder will run fiohistogram.py on each logfile and generate 
# histogram graphs showcasing both pdfs and cdfs

# do platform-specific setup
case "$(uname -s)" in
    Darwin) echo 'Mac OS X';;
    Linux) echo 'Linux';;
    CYGWIN*|MINGW32*|MSYS*|MINGW*)
        echo 'MS Windows'
        alias python3=python
        ;;
esac

# ask users to provide filepath for folder and pattern strings
# name pattern for log files: [jobname]_[metric].[jobnumber].log 
HOME_FOLDER=$1
METRIC=$2
JOBNAME=$3
if [ -z "${HOME_FOLDER}" ]; then
    echo "Enter HOME_FOLDER for log files:"
    read HOME_FOLDER    # /D/qd-1/nj8
fi
if [ -z "${METRIC}" ]; then
    echo "Enter log METRIC name (ex. bw, lat, iops):"
    read METRIC
fi
if [ -z "${JOBNAME}" ]; then
    echo "Enter JOBNAME (ex. seq-read):"
    read JOBNAME
fi

# go through log files and run fiohistogram.py on each
shopt -s nullglob
files=(${HOME_FOLDER}/*${JOBNAME}_${METRIC}.*.log)
for f in ${files[@]}
do 
    name="$(basename -s .log $f)"
    python3 ../src/fiohistogram.py -lt "${METRIC}" -f "$f" -m simple -o "$name-hist.png" --bins 100
    python3 ../src/fiohistogram.py -lt "${METRIC}" -f "$f" -m simple -o "$name-hist-ylog.png" --bins 100 --ylog
    python3 ../src/fiohistogram.py -lt "${METRIC}" -f "$f" -m simple -o "$name-cdf.png" --bins 100 -hm cdf
    # python3 ../src/fiohistogram.py -lt "${METRIC}" -f "$f" -m normal -o "$name-hist-normal.png" --bins 100 -v
    # warning enabling the next line will slow down execution considerably due to model training - use limit and/or cutoff to reduce dataset
    # python3 ../src/fiohistogram.py -lt "${METRIC}" -f "$f" -m kernel -o "$name-hist-kernel.png" --bins 100 -v -c 20 -ll 0.1 -kbw 0.5
done