#!/bin/sh
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
	sh graph-builder.sh "$HOME_FOLDER" "lat" "*"
	zip -m $name.zip $f $name.txt *.log *.png !(output.png) # zip all related files and remove them from drive
	echo "$name has completed."
done
echo "Experimentation complete. Please transfer and remove zip files."