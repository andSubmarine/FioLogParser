#!/usr/bin/env bash
# The exp-runner script will look in a given folder, run all experiments found, pack the results into a zip and perform cleanup
HOME_FOLDER=$1
if [ -z "${HOME_FOLDER}" ]; then
    echo "Enter HOME_FOLDER for log files:"
    read HOME_FOLDER    # /D/qd-1/nj8
fi
echo "Starting experimentation"
shopt -s nullglob
files=(${HOME_FOLDER}/*.fio)
for f in ${files[@]}
do 
	name="$(basename -s .fio $f)"	# filename without type
	echo "Executing $name..."
	fio $f > $name.txt	# run experiment
	logfiles=(${HOME_FOLDER}/*_lat.*.log)
	for lf in ${logfiles[@]}
	do
		python3 ../src/fiologparser.py -m io_count -lt lat --title "IOPS distribution over the course of experiment" --every_nth 1000 --same_time -o "$name-iocount.png" -f "$lf"
		python3 ../src/fiologparser.py -m ios -lt lat --title "Measurement value per I/O" -o "$name-ios-ylog.png" -f "$lf" -ylog
		python3 ../src/fiohistogram.py -m simple -lt lat -f "$lf" -o "$name-hist.png" --bins 100
		python3 ../src/fiohistogram.py -m simple -lt lat -f "$lf" -o "$name-hist-ylog.png" --bins 100 --ylog
	done
	zip -m $name.zip $f $name.txt *.log $name*.png  # zip all related files and remove them from drive
	echo "$name has completed."
done
echo "Experimentation complete. Please transfer and remove zip files."
