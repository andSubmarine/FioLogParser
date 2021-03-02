import sys
import os
import re
import time
import math
import argparse

from fio_utils import file_check

def find_max_from_files(files): 
    currentMaxValue = 0
    for i in range(len(files)):
        filepath = files[i]
        with open(filepath) as f:
            for i, line in enumerate(f):
                nextLatencyArray = re.split(", ", line)
                nextLatency = (int(nextLatencyArray[1])) / 1000
                if(nextLatency > currentMaxValue):
                    currentMaxValue = nextLatency
    
    return currentMaxValue

def find_iopsmax(files):
    maxNumberOfTraces = 0
    for i in range(len(files)):
        filepath = files[i]
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
                    
    return maxNumberOfTraces

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f','--files', nargs='+', help='absolute/relative filepaths for files to parse', required=True)
    parser.add_argument('--iopsmax',  action='store_true', help='change from finding max value to finding maximum iops value')
    parser.add_argument('-v', '--verbose',  action='store_true', help='print more information')
    args = parser.parse_args()

    maxValue = 0
    if(args.iopsmax):
        maxValue = find_iopsmax(args.files)
    else:    
        maxValue = find_max_from_files(args.files)
    
    maxValue = int(math.ceil(maxValue))

    if args.verbose:
        print("Max value found across '{}' files was '{}'".format(len(args.files), maxValue))
    else:
        print(maxValue)
    
if __name__ == '__main__':
    main()