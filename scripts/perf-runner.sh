#!/usr/bin/env bash

# 1) Setup
HOME_FOLDER=$1
if [ -z "${HOME_FOLDER}" ]; then
    echo "Enter directory for Fio files:"
    read HOME_FOLDER    # /D/qd-1/nj8
fi
shopt -s nullglob
files=(${HOME_FOLDER}/*.fio)

echo "Starting Fio"

# 2) run: run each fio experiment
for f in ${files[@]}
do
        name="$(basename -s .fio $f)"   # filename without type
        echo "Executing $name..."
        fio $f > $name.txt &       # run experiment
        mypid=$!
        sleep 150
        perf stat -p $mypid -o $name.perf.txt -e instructions,cpu_clk_unhalted.thread,cs,migrations,faults,frontend_retired.l1i_miss,frontend_retired.l2_miss,offcore_response.demand_code_rd.l3_miss.any_snoop,mem_load_retired.l1_miss,mem_load_retired.l2_miss,mem_load_retired.l3_miss,br_misp_retired.all_branches,dTLB-load-misses,mem_inst_retired.stlb_miss_loads,frontend_retired.stlb_miss,frontend_retired.itlb_miss sleep 180
        echo "$name has completed."
done

echo "Experiment Done"
