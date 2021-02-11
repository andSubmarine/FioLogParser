import os
import sys
import time
import re
import numpy as np

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