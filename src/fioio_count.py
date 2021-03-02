import sys
import re
import time
import math

import numpy as np
import matplotlib
import matplotlib.pyplot as plt

from line_count import line_count
from fio_utils import metric_label, combine, simply_filename, every_nth, not_same_every_nth, file_check, time_it, elapsed_time_string

###################################################
# IO COUNT MODE
###################################################
def build_io_count_graph(args, ax, results):
    for (y_values, x_values) in results:
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
        else:
            if(args.axisalign):
                ax.set_ylim(bottom=0, top=args.axisalign)
            else:
                ax.set_ylim(bottom=0)

def build_io_count_graphs(args):
    fig, ax = plt.subplots()
    results = np.empty(len(args.files), dtype=object)
    for i in range(len(args.files)):
        filepath = args.files[i]
        file_check(filepath)
        results[i] = time_it(load_input_for_io_count, args.verbose, args, filepath, start_tag="", end_tag="Input load time")
    build_io_count_graph(args, ax, combine(results) if args.aggregate_files else results)
    if args.aggregate_files:
        ax.legend([", ".join([simply_filename(f) for f in args.files]) if len(args.files) < 3 else "aggregated files"], loc="upper right")
    else: 
        ax.legend([simply_filename(f) for f in args.files], loc="upper right")
    ax.set(xlabel="Elapsed time ({})".format(elapsed_time_string(args)),
           ylabel="IOPS",
           title=args.title)
    ax.grid()
    plt.tight_layout()
    fig.savefig(args.output)
    plt.close()

def load_input_for_io_count(args, filepath):
    lc = time_it(line_count, args.verbose, filepath, start_tag="Reading lines in file...", end_tag="Line Count Time") + 1
    print("Lines in file: {}".format(lc))
    start_time = time.time_ns()
    y_values = np.zeros([lc])
    x_values = np.arange(1,lc)
    k = 0
    if args.verbose:
        print("Starting reading input...")
    ThousandCounter = 1000
    with open(filepath) as f:        
        line_fraction = int(math.ceil(lc / 1E2))
        last = 0
        count = 0
        for i, line in enumerate(f):
            log = re.split(", ", line)
            nextTime = (int(log[0]))
            if(nextTime <= ThousandCounter):
                count +=1
            elif(nextTime > ThousandCounter):
                y_values[k] = count
                count = 0
                ThousandCounter += 1000
                k += 1
            if(i % line_fraction == 0):
                time_now = time.time_ns()
                print("Progress: {:.0f}% ({:.3f} msec)".format(((i / lc) * 100), (time_now - start_time) / 1E6),end="\r")
                start_time = time_now
    print()
    return (y_values[:k], x_values[:k])