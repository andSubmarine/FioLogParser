import time
import argparse

from fioelapsed import build_elapsed_graphs
from fioios import build_count_graphs
from fioio_count import build_io_count_graphs
from fiomixed import build_mixed_read_write_graphs

###################################################
# MAIN METHOD & ARGUMENTS
###################################################
def main():
    """ 
    FioLogParser will generate a plot from a fio log file. This file is to be used as a unifying interface to a class of python scripts 
    such as fioio_count, fioios, fioelapsed and fiohistogram. 
    """
    print("Welcome to FioLogParser!")
    parser = argparse.ArgumentParser()
    parser.add_argument('-m','--mode', help="the mode used for parsing and building graphs", 
                        choices=["elapsed", "ios","io_count", "mixed"], required=True)
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
    parser.add_argument('-aa','--axisalign', help="a single number determining the max value across log files in order to align the axis",
                        type=int)

    args = parser.parse_args()
    start_time = time.time_ns()

    print("Building graph '{}' in mode '{}' as a '{}' graph from '{}' log file(s)".format(args.output, args.mode, args.graphtype, args.logtype))
    if args.mode == "elapsed":
        build_elapsed_graphs(args)
    elif args.mode == "ios":
        build_count_graphs(args)
    elif args.mode == "io_count":
        build_io_count_graphs(args)
    elif args.mode == "mixed":
        build_mixed_read_write_graphs(args)
    print("Completed turning log file(s) into graphs ({:.3f} sec).".format((time.time_ns() - start_time) / 1E9))

if __name__ == '__main__':
    main()
