#!/bin/sh
# The exp-runner script will look in a given folder, run all experiments found, pack the results into a zip and perform cleanup
echo "Enter filepath of fio experiment files:"
read HOME_FOLDER    # ex: /D/qd-1/nj8
echo "Starting experimentation"
shopt -s nullglob
files=(${HOME_FOLDER}/*.fio)
for f in ${files[@]}
do 
	name="$(basename -s .fio $f)"	# filename without type
	fio $f > $name.txt	# run experiment
	zip -m $name.zip $f $name.txt *.logs # zip all related files and remove them from drive
	echo "$name has completed."
done
echo "Experimentation complete. Please transfer and remove zip files."