import sys
import re
import time
import math

import numpy as np
import matplotlib
import matplotlib.pyplot as plt

from line_count import line_count
from fio_utils import metric_label, simply_filename, file_check, time_it


###################################################
# MIXED MODE
###################################################
def build_mixed_read_write_graphs(args):
    ylabel = metric_label(args.logtype)
    for i in range(len(args.files)):
        filepath = args.files[i]
        file_check(filepath)
        (reads, writes, x_values) = time_it(load_input_for_count, args.verbose, args, filepath, start_tag="",end_tag="Input load time")
        build_graph(args, x_values, reads, filepath, mode="reads")
        build_graph(args, x_values, writes, filepath, mode="writes")

def build_graph(args, x_values, y_values, filepath, mode="reads"):
    ylabel = metric_label(args.logtype)
    fig, ax = plt.subplots()
    if args.graphtype == "errorbar":
        print("errorbar not supported for this mode")
        sys.exit()
    elif args.graphtype == "bar":
        ax.bar(x_values, y_values, width=0.05)
    elif args.graphtype == "line":
        ax.plot(x_values, y_values)
    else:
        ax.scatter(x_values, y_values, s=10)
    if args.logscale_y:
        ax.set_yscale('log')
        ax.set_ylim(bottom=1)
    else:
        ax.set_ylim(bottom=0)
    if(args.axisalign):
        ax.set_ylim(top=args.axisalign)

    ax.set_xlim(left=0, right=len(x_values))        
    legend=mode+"-"+simply_filename(filepath)
    ax.legend([legend], loc="upper right")
    ax.set(xlabel="IO Number (counted by log entries)",ylabel=ylabel,title=args.title)
    ax.grid()
    # plt.tight_layout()
    fig.savefig(mode+"-"+args.output)
    plt.close()

def load_input_for_count(args, filepath):
    lc = time_it(line_count, args.verbose, filepath, start_tag="Reading lines in file...", end_tag="Line Count Time") + 1
    print("Lines in file: {}".format(lc))
    start_time = time.time_ns()
    x_values = np.arange(lc)
    reads = np.zeros([lc])
    writes = np.zeros([lc])
    k = 0
    if args.verbose:
        print("Starting reading input...")
    with open(filepath) as f:        
        line_fraction = int(math.ceil(lc / 1E2))
        for i, line in enumerate(f):
            log = re.split(", ", line)
            if int(log[2]) == 0:
                reads[k] = int(log[1]) / 1000
                writes[k] = np.NaN
            elif int(log[2]) == 1:
                writes[k] = int(log[1]) / 1000
                reads[k] = np.NaN
            k += 1
            if(i % line_fraction == 0):
                time_now = time.time_ns()
                print("Progress: {:.0f}% ({:.3f} msec)".format(((i / lc) * 100), (time_now - start_time) / 1E6),end="\r")
                start_time = time_now
    print()
    return (reads[:k], writes[:k], x_values[:k])