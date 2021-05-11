#!/bin/sh

# 1) Setup
HOME_FOLDER=$1
if [ -z "${HOME_FOLDER}" ]; then
    echo "Enter directory for Fio files:"
    read HOME_FOLDER    # /D/qd-1/nj8
fi
shopt -s nullglob
files=(${HOME_FOLDER}/*.fio)

echo "Starting Fio"

# 2) run: run each fio experiment using perf to record traces for flamegraph
for f in ${files[@]}
do
        name="$(basename -s .fio $f)"   # filename without type
        echo "Executing $name..."
        fio $f > $name.txt &       # run experiment
        mypid=$!
        sleep 1
        perf record -F 99 -g --call-graph dwarf -p $mypid sleep 240
        perf script > out.perf
        
        #NOTE: FlameGraph is expected, by default, to be in the same directory as this flamegraph.sh script.
        #Change location of FlameGraph if the library is installed elsewhere.
        #fold stacks
        ./FlameGraph/stackcollapse-perf.pl out.perf > perf.folded

        # make svg graph
        ./FlameGraph/flamegraph.pl perf.folded > $name.svg
        
        echo "$name has completed."
done

echo "Experiment Done"
