import sys
import os
import math
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import time
import re
import argparse
from line_count import line_count
import string

###################################################
# MAIN METHOD & ARGUMENTS
###################################################
def main():
    """ 
    FioLogParser will generate a plot from a fio log file.
    usage: fiologparser.py [-h] -m {elapsed,ios,io_count} -lt {bw,lat,iops} -f FILES [FILES ...]
                       [-o OUTPUT] [--title TITLE] [-v] [--every_nth EVERY_NTH]
                       [--same_time] [-ylog] [-agg] [-gt {default,bar,line,dots,errorbar}]
    Log format: 
    time (msec), value, data direction, block size (bytes), (offset (bytes)), command priority
    
    The value logged depends on the type of log:
    - lat: Value is latency in nsecs
    - bw: Value is bandwidth in KiB/sec
    - iops: Value is in IOPS
    Data direction is either 0 (READ), 1 (WRITE) or 2 (TRIM)
    """
    print("Welcome to FioLogParser!")
    parser = argparse.ArgumentParser()
    parser.add_argument('-m','--mode', help="the mode used for parsing and building graphs", 
                        choices=["elapsed", "ios","io_count"], required=True)
    parser.add_argument('-lt','--logtype', help="the type for values in files", 
                        default="bw", choices=["bw","lat","iops"],required=True)
    parser.add_argument('-f','--files', nargs='+', help='absolute/relative filepaths for files to parse', required=True)
    parser.add_argument('-o','--output', help="filepath for the built graph. defaults to 'output.png'", default="output.png")
    parser.add_argument('--title', help="the title of the built graph", default="Fio Log Experiment")
    parser.add_argument('-v','--verbose', help="print more information while running script", default=False, action='store_true')
    parser.add_argument("--every_nth", type=int, default=1,
                        help="iterate over n values. used for mode 'elapsed' and 'io_count'. defaults to 1")
    parser.add_argument('--same_time',default=False, action='store_true', help="specify that iterations should occur based on time")
    parser.add_argument('-ylog','--logscale_y',default=False, action='store_true', help="use a logirithm scale instead of a linear scale for the y-axis")
    parser.add_argument('-agg','--aggregate_files',default=False, action='store_true', help="aggregate results from multiple logs into a single data set")
    parser.add_argument('-gt','--graphtype', help="the type of graph to be built. defaults to a mode-specific default", 
                        default="default", choices=["default","bar","line","dots","errorbar"])
    args = parser.parse_args()
    start_time = time.time_ns()
    print("Building graph '{}' in mode '{}' as a '{}' graph from '{}' log file(s)".format(args.output, args.mode, args.graphtype, args.logtype))
    if args.mode == "elapsed":
        build_elapsed_graphs(args)
    elif args.mode == "ios":
        build_count_graphs(args)
    elif args.mode == "io_count":
        build_io_count_graphs(args)
    print("Completed turning log file(s) into graphs ({:.3f} sec).".format((time.time_ns() - start_time) / 1E9))

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

###################################################
# IOS MODE
###################################################
def build_count_graphs(args):
    ylabel = determine_ylabel(args.logtype)
    fig, ax = plt.subplots()
    for i in range(len(args.files)):
        filepath = args.files[i]
        file_check(filepath)
        (y_values, x_values) = time_it(load_input_for_count, args.verbose, args, filepath, start_tag="",end_tag="Input load time")
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
    ax.legend([simply_filename(f) for f in args.files], loc="upper right")
    ax.set(xlabel="IO Number (counted by log entries)",ylabel=ylabel,title=args.title)
    ax.grid()
    # plt.tight_layout()
    fig.savefig(args.output)
    plt.close()

def load_input_for_count(args, filepath):
    lc = time_it(line_count, args.verbose, filepath, start_tag="Reading lines in file...", end_tag="Line Count Time") + 1
    print("Lines in file: {}".format(lc))
    start_time = time.time_ns()
    y_values = np.zeros([lc])
    x_values = np.arange(lc)
    k = 0
    if args.verbose:
        print("Starting reading input...")
    with open(filepath) as f:        
        line_fraction = int(math.ceil(lc / 1E2))
        for i, line in enumerate(f):
            log = re.split(", ", line)
            y_values[k] = int(log[1]) / 1000
            k += 1
            if(i % line_fraction == 0):
                time_now = time.time_ns()
                print("Progress: {:.0f}% ({:.3f} msec)".format(((i / lc) * 100), (time_now - start_time) / 1E6),end="\r")
                start_time = time_now
    print()
    return (y_values[:k], x_values[:k])

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
    with open(filepath) as f:        
        line_fraction = int(math.ceil(lc / 1E2))
        last = 0
        count = 0
        for i, line in enumerate(f):
            log = re.split(", ", line)
            if (i == 0):
                last = int(log[0])
                count += 1
            # if not same value or trace is the last then output count and reset
            elif ((i == (lc-1)) or 
                not_same_every_nth(int(log[0]), last, args.every_nth)):
                y_values[k] = count
                k += 1
                last = int(log[0])
                count = 1
            else:
                count += 1
            if(i % line_fraction == 0):
                time_now = time.time_ns()
                print("Progress: {:.0f}% ({:.3f} msec)".format(((i / lc) * 100), (time_now - start_time) / 1E6),end="\r")
                start_time = time_now
    print()
    return (y_values[:k], x_values[:k])

###################################################
# UTILITY FUNCTIONS
###################################################

def every_nth(x, n, off=0):
    return x % n == off

def not_same(x,y):
    return x != y

def not_same_every_nth(x, y, n, off=0):
    return not_same(x,y) and every_nth(x,n,off=off)

def time_it(process, verbose, *args, start_tag="", end_tag="Time"):
    """
    Times a process given args in msec
    start_tag and end_tag is printed before and after the process is called
    """
    if verbose:
        if start_tag != "":
            print(start_tag)
        start_time = time.time_ns()
        output = process(*args)
        end_time = time.time_ns()
        print("{}: {:.3f} sec".format(end_tag,(end_time - start_time) / 1E9))
        return output
    else:
        return process(*args)

def determine_ylabel(log_type):
    if (log_type == "bw"):
        return "Bandwidth (MiB/sec)" #MiB instead of KiB due to division by 1000
    elif (log_type == "lat"):
        return "Latency (usec)" #usec instead of nsec due to division by 1000
    elif (log_type == "iops"):
        return "Thousand IOs Per Second" 
    else:
        return "Value"

def file_check(file):
    if not os.path.isfile(file):
        print("File path {} does not exist. Exiting...".format(file))
        sys.exit()
    else:
        print("Found file '{}'. Starting processing...".format(file.split("/")[-1]))

def elapsed_time_string(args):
    if (args.every_nth == 1000):
        return "sec"
    elif (args.every_nth == 1):
        return "msec"
    else:
        return "{} sec".format(args.every_nth/1000)

def combine(results):
    # prepare for data extraction by building a 3-dimensional array of [result set, x/y, data]
    split_values = np.split(results,len(results))
    length = max([len(val[0][0]) for val in split_values])
    values = [np.array(arr[0]) for arr in split_values]
    # extract x_values by finding unique x values across result sets
    x_filter = np.concatenate([v[1] for v in values])
    x_values = np.unique(x_filter)
    # extract y_values by summing y values across result sets
    y_filter = [np.array(v[0]) if len(v[0]) == length else np.concatenate([v[0],np.zeros(length-len(v[0]))]) for v in values]
    y_values = np.sum(y_filter, axis=0)
    return [(y_values,x_values)]

def simply_filename(filename):
    filenames = re.split(r"[\/\\]", filename)
    return filenames[-1] 

if __name__ == '__main__':
    main()
