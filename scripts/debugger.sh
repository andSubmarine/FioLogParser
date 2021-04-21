#!/usr/bin/env bash
# 1) setup: specify where fio experiment configuration files are located
HOME_FOLDER=$1
if [ -z "${HOME_FOLDER}" ]; then
	echo "Enter HOME_FOLDER for log files:"
	read HOME_FOLDER    # /D/qd-1/nj8
fi
echo "Starting experimentation"
shopt -s nullglob
files=(${HOME_FOLDER}/*.fio)

# 2) run: run each fio experiment configuration and store results and log files locally
for f in ${files[@]}
do
        name="$(basename -s .fio $f)"   # filename without type
        echo "Executing $name..."
        /home/pito/xNVMe/third-party/fio/repos/fio $f --debug=all  > $name.txt       # run experiment
        echo "$name has completed."
done
