import sys
import os
import re
import time
import math
import argparse

from fio_utils import file_check

def find_max_from_files(files, verbose=False): 
    currentMaxValue = 0
    for i in range(len(files)):
        filepath = files[i]
        start_time=time.time_ns()
        if verbose:
            print("Processing {}...".format(filepath))
        with open(filepath) as f:
            for i, line in enumerate(f):
                nextLatencyArray = re.split(", ", line)
                nextLatency = (int(nextLatencyArray[1])) / 1000
                if(nextLatency > currentMaxValue):
                    currentMaxValue = nextLatency
        if verbose:
            print("Processed {} in {:.3f} sec.".format(filepath,(time.time_ns() - start_time) / 1E9))
    return int(math.ceil(currentMaxValue))

def find_iopsmax(files, verbose=False):
    maxNumberOfTraces = 0
    for i in range(len(files)):
        filepath = files[i]
        start_time=time.time_ns()
        if verbose:
            print("Processing {}...".format(filepath))
        ThousandCounter = 1000
        with open(filepath) as f:
            numberOfTraces = 0
            for i, line in enumerate(f):
                nextLineArray = re.split(", ", line)
                nextTime = (int(nextLineArray[0]))
                if(nextTime <= ThousandCounter):
                    numberOfTraces +=1
                elif(nextTime > ThousandCounter):
                    if(numberOfTraces > maxNumberOfTraces):
                        maxNumberOfTraces = numberOfTraces
                    numberOfTraces = 0
                    ThousandCounter += 1000
            if(numberOfTraces > maxNumberOfTraces):
                maxNumberOfTraces = numberOfTraces
                    
        if verbose:
            print("Processed {} in {:.3f} sec.".format(filepath,(time.time_ns() - start_time) / 1E9))
    return int(math.ceil(maxNumberOfTraces))

def find_max_and_iops(files, verbose=False):
    maxNumberOfTraces = 0
    currentMaxValue = 0
    for i in range(len(files)):
        filepath = files[i]
        start_time=time.time_ns()
        if verbose:
            print("Processing {}...".format(filepath))
        ThousandCounter = 1000
        with open(filepath) as f:
            numberOfTraces = 0
            for i, line in enumerate(f):
                nextLineArray = re.split(", ", line)
                nextLatency = (int(nextLineArray[1])) / 1000
                nextTime = (int(nextLineArray[0]))
                if(nextTime <= ThousandCounter):
                    numberOfTraces +=1
                elif(nextTime > ThousandCounter):
                    if(numberOfTraces > maxNumberOfTraces):
                        maxNumberOfTraces = numberOfTraces
                    numberOfTraces = 0
                    ThousandCounter += 1000
                if(nextLatency > currentMaxValue):
                    currentMaxValue = nextLatency
            if(numberOfTraces > maxNumberOfTraces):
                maxNumberOfTraces = numberOfTraces
        if verbose:
            print("Processed {} in {:.3f} sec.".format(filepath,(time.time_ns() - start_time) / 1E9))
                    
    return (int(math.ceil(currentMaxValue)), int(math.ceil(maxNumberOfTraces)))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f','--files', nargs='+', help='absolute/relative filepaths for files to parse', required=True)
    parser.add_argument('-m','--mode', help="the mode of operation determines if the maximum value, the maxium iops value or both should be produced by the run. defaults to 'max'", 
                        default="max", choices=["max","iops","both"])
    parser.add_argument('-v', '--verbose',  action='store_true', help='print more information')
    args = parser.parse_args()

    maxValue = 0
    maxTraces = 0
    start_time = time.time_ns()
    if args.mode == "max":
        maxValue = find_max_from_files(args.files, verbose=args.verbose)
        if args.verbose:
            print("Max value found across '{}' files was '{}'".format(len(args.files), maxValue))
            print("Found max value in {:.3f} sec.".format((time.time_ns() - start_time) / 1E9))
        else:
            print(maxValue)
    elif args.mode == "iops":
        maxTraces = find_iopsmax(args.files, verbose=args.verbose)
        if args.verbose:
            print("Max IOPS value found across '{}' files was '{}'".format(len(args.files), maxTraces))
            print("Found max IOPS value in {:.3f} sec.".format((time.time_ns() - start_time) / 1E9))
        else:
            print(maxValue)
    else:
        (maxValue, maxTraces) = find_max_and_iops(args.files, verbose=args.verbose)
        if args.verbose:
            print("Max value found across '{}' files was '{}'".format(len(args.files), maxValue))
            print("Max IOPS value found across '{}' files was '{}'".format(len(args.files), maxTraces))
            print("Found max values in {:.3f} sec.".format((time.time_ns() - start_time) / 1E9))
        else:
            print("{} {}".format(maxValue, maxTraces))

    
if __name__ == '__main__':
    main()