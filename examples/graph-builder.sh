#!/usr/bin/env bash
# Given a folder and arguments to find log files, the graph-builder will run both fiologparser.py and fiohistogram.py on each logfile and generate 
# the most typical graphs

# do platform-specific setup
case "$(uname -s)" in
    Darwin) echo 'Mac OS X';;
    Linux) echo 'Linux';;
    CYGWIN*|MINGW32*|MSYS*|MINGW*)
        echo 'MS Windows'
        alias python3=python
	shopt -s nullglob
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

# go through log files and run FioLogparser and FioHistogram on each
files=(${HOME_FOLDER}/*${JOBNAME}_${METRIC}.*.log)
echo "Find MAX and MAX_IOPS in '${files[@]}'..."
maxes=$(python3 ../src/max_value_finder.py -f ${files[@]} -m both 2>&1)
max=$(echo $maxes | cut -f1 -d " ")
iops=$(echo $maxes | cut -f2 -d " ")
echo "MAX=$max"
echo "MAX_IOPS=$iops"
for f in ${files[@]}
do 
    name="$(basename -s .log $f)"
    echo "Processing $name..."
    python3 ../src/fiologparser.py -m io_count -lt "${METRIC}" --title "IOPS distribution over the course of experiment" -o "$name-iocount.png" -f "$f" -aa "$iops"
    python3 ../src/fiologparser.py -m ios -lt "${METRIC}" --title "Measurement value per I/O" -o "$name-ios-ylog.png" -f "$f" -ylog -aa "$max"
    python3 ../src/fiohistogram.py -lt "${METRIC}" -f "$f" -m simple -o "$name-hist.png" --bins 100 --min 0 --max "$max"
    python3 ../src/fiohistogram.py -lt "${METRIC}" -f "$f" -m simple -o "$name-hist-ylog.png" --bins 100 --ylog --min 0 --max "$max"
    echo -e "$name complete\n"
done
echo "done"
