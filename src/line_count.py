import sys
import os
import time
from fio_utils import file_check

def line_count(filepath): 
    with open(filepath) as f:
        i = -1
        for i, l in enumerate(f):
            pass
    return i

def main():
    filepath = sys.argv[1]

    file_check(filepath)
    
    start_time = time.time_ns()
    print("Starting line count of '{}'".format(filepath))
    print("Lines in file: {}".format(line_count(filepath) + 1))
    print("Time: {:.0f} nsec".format(time.time_ns() - start_time))
    
if __name__ == '__main__':
    main()