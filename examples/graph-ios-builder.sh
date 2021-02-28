#!/bin/sh
# Given a folder and arguments to find log files, the graph-ios-builder will run fiologparser.py on each logfile and generate 
# graphs that shows the how metric measurements change over each I/O being performed - with a logarithmic y-axis

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
read HOME_FOLDER    # ex: /D/qd-1/nj8
echo "Enter log metric name (ex. bw, lat, iops):"
read METRIC
echo "Enter jobname (ex. seq-read):"
read JOBNAME

# go through log files and run fiologparser.py in io_count mode on each
shopt -s nullglob
files=(${HOME_FOLDER}/*${JOBNAME}_${METRIC}.*.log)
for f in ${files[@]}
do 
    name="$(basename -s .log $f)"
    # python3 ../src/fiologparser.py -m ios -lt "${METRIC}" --title "Measurement value per I/O" -o "$name-ios.png" -f "$f"
    python3 ../src/fiologparser.py -m ios -lt "${METRIC}" --title "Measurement value per I/O" -o "$name-ios-ylog.png" -f "$f" -ylog
done
echo "done"