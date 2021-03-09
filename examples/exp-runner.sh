#!/usr/bin/env bash
# The exp-runner script will look in a given folder, run all experiments found, pack the results into a zip and perform cleanup
# 1) setup: specify where fio experiment configuration files are located
HOME_FOLDER=$1
if [ -z "${HOME_FOLDER}" ]; then
    echo "Enter HOME_FOLDER for log files:"
    read HOME_FOLDER    # /D/qd-1/nj8
fi
echo "Starting experimentation"
shopt -s nullglob
files=(${HOME_FOLDER}/*.fio)
if [-z "$files"]; then
	exit 1 # no files found so don't do the rest
fi
# 2) run: run each fio experiment configuration and store results and log files locally
for f in ${files[@]}
do 
	name="$(basename -s .fio $f)"	# filename without type
	echo "Executing $name..."
	/home/pito/xNVMe/third-party/fio/repos/fio $f > $name.txt	# run experiment
	echo "$name has completed."
done

# 3) make graphs: all experiments has been run and log files have been flushed so build graphs like in graph-builder.sh
#for f in ${files[@]}
#do 
#	name="$(basename -s .fio $f)"	# filename without type
#	logfiles=(*_lat.*.log)
#	echo "Find MAX and MAX_IOPS in $logfiles..."
#	echo "Find MAX and MAX_IOPS in '${logfiles[@]}'..."
#	maxes=$(python3 ../src/max_value_finder.py -f ${logfiles[@]} -m both 2>&1)
#	max=$(echo $maxes | cut -f1 -d " ")
#	iops=$(echo $maxes | cut -f2 -d " ")
#	echo "MAX=$max"
#	echo "MAX_IOPS=$iops"
#	for lf in ${logfiles[@]}
#	do
#		python3 ../src/fiologparser.py -m io_count -lt lat --title "IOPS distribution over the course of experiment" -o "$name-iocount.png" -f "$lf"  -aa "$iops" 
#		python3 ../src/fiologparser.py -m ios -lt lat --title "Measurement value per I/O" -o "$name-ios-ylog.png" -f "$lf" -ylog -aa "$max"
#		python3 ../src/fiohistogram.py -m simple -lt lat -f "$lf" -o "$name-hist.png" --bins 100 --min 0 --max "$max"
#		python3 ../src/fiohistogram.py -m simple -lt lat -f "$lf" -o "$name-hist-ylog.png" --bins 100 --ylog --min 0 --max "$max"
#	done
#done

# 4) cleanup: zip all related files and remove them from drive
#for f in ${files[@]}
#do 
#	name="$(basename -s .fio $f)"	# filename without type
#	zip -m ${HOME_FOLDER}/$name.zip $f $name.txt $name*.log $name*.png
#	echo "$name has been zipped."
#done
echo "Experimentation complete. Please transfer and remove zip files."
