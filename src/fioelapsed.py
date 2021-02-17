import sys
import re
import time
import math

import numpy as np
import matplotlib
import matplotlib.pyplot as plt

from line_count import line_count
from fio_utils import determine_ylabel, combine, simply_filename, every_nth, not_same_every_nth, file_check, time_it, elapsed_time_string

###################################################
# ELAPSED MODE
###################################################
def build_elapsed_graphs(args):
    ylabel = determine_ylabel(args.logtype)
    fig, ax = plt.subplots()

    for i in range(len(args.files)):
        filepath = args.files[i]
        file_check(filepath)
        (y_values, x_values, y_lows, y_highs) = time_it(load_input_for_elapsed, args.verbose, args, filepath, start_tag="",end_tag="Input load time")

        if args.graphtype == "dots":
            ax.scatter(x_values,y_values, s=10)
        elif args.graphtype == "line":
            ax.plot(x_values,y_values)
        elif args.graphtype == "bar":
            print("bar graph not supported for this mode")
            sys.exit()
        else:
            ax.errorbar(x_values,y_values,yerr=[y_lows, y_highs], fmt='o', linewidth=1, markersize=5)
        if args.logscale_y:
            ax.set_yscale('log')
        else:
            ax.set_ylim(bottom=0)
    ax.legend([simply_filename(f) for f in args.files], loc="upper right")
    ax.set(xlabel="Elapsed time (sec)", ylabel=ylabel,title=args.title)
    ax.grid()
    # plt.tight_layout()
    fig.savefig(args.output)
    plt.close()

def load_input_for_elapsed(args, filepath):
    """
    Loads and parses the input from the given filepath. 
    Returns a 4-tuple of (y_values, x_values, y_lows, y_highs) 
    where y_values are the average values of the experiment, 
    x_values are the elapsed time in msec for the average values, 
    y_lows are the lowest y values per elapsed time, and y_highs 
    are the highest y values per elapsed time.
    """
    lc = time_it(line_count, args.verbose, filepath, start_tag="Reading lines in file...", end_tag="Line Count Time") + 1
    print("Lines in file: {}".format(lc))
    start_time = time.time_ns()
    y_values = np.zeros([lc,1])
    x_values = np.zeros([lc,1])
    y_lows = np.zeros([lc])
    y_highs = np.zeros([lc])
    k = 0
    if args.verbose:
        print("Starting reading input...")
    with open(filepath) as f:
        line_fraction = int(math.ceil(lc / 1E2))
        counter = 0
        time_now = 0
        log = []
        y_sum = 0
        y_low = 0 
        y_high = 0
        x_last = 0
        j = 1
        for i, line in enumerate(f):
            log = re.split(", ", line)
            if (i == 0):
                y_sum += int(log[1])
                y_high = int(log[1])
                y_low = int(log[1])
                j += 1
            elif ((i == (lc-1)) or 
                 (not args.same_time and every_nth(int(log[0]), args.every_nth)) 
                 or (args.same_time and not_same_every_nth(int(log[0]), x_last, args.every_nth))):
                y_avg = y_sum / j
                y_values[k] = y_avg / 1000
                x_values[k] = x_last / 1000
                y_lows[k] = y_low / 1000
                y_highs[k] = y_high / 1000
                y_sum = int(log[1])
                y_high = int(log[1])
                y_low = int(log[1])
                j = 1
                k += 1
            else:
                y_sum += int(log[1])
                if (int(log[1]) < y_low):
                    y_low = int(log[1])
                if (int(log[1]) > y_high):
                    y_high = int(log[1])
                j += 1
            x_last = int(log[0])
            if(counter % line_fraction == 0):
                time_now = time.time_ns()
                print("Progress: {:.0f}% ({:.3f} msec)".format(((counter / lc) * 100), (time_now - start_time) / 1E6),end="\r")
                start_time = time_now
            counter += 1
    print()
    return (y_values[:k,:], x_values[:k,:], y_lows[:k], y_highs[:k])