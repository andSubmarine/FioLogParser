#!/bin/sh
# Given a folder and arguments to find log files, the graph-builder will run both fiologparser.py and fiohistogram.py on each logfile and generate 
# the most typical graphs

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
echo "Enter folder containing log files:"
read HOME_FOLDER    # /D/qd-1/nj8
echo "Enter log metric name (ex. bw, lat, iops):"
read METRIC
echo "Enter jobname (ex. seq-read):"
read JOBNAME

# go through log files and run fiohistogram.py on each
shopt -s nullglob
files=(${HOME_FOLDER}/*${JOBNAME}_${METRIC}.*.log)
for f in ${files[@]}
do 
    name="$(basename -s .log $f)"
    echo "Processing $name..."
    python3 ../src/fiologparser.py -m io_count -lt "${METRIC}" --title "IOPS distribution over the course of experiment" --every_nth 1000 --same_time -o "$name-iocount.png" -f "$f"
    python3 ../src/fiologparser.py -m ios -lt "${METRIC}" --title "Measurement value per I/O" -o "$name-ios-ylog.png" -f "$f" -ylog
    python3 ../src/fiohistogram.py -lt "${METRIC}" -f "$f" -m simple -o "$name-hist.png" --bins 100
    python3 ../src/fiohistogram.py -lt "${METRIC}" -f "$f" -m simple -o "$name-hist-ylog.png" --bins 100 --ylog
    echo -e "$name complete\n"
done
echo "done"