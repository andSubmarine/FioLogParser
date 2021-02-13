import re
import time
import argparse
import math

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from scipy.stats import norm
from sklearn.neighbors import KernelDensity
from sklearn.model_selection import GridSearchCV

from line_count import line_count
from fio_utils import time_it

def load(args, filepath): 
    lc = time_it(line_count, args.verbose, filepath, start_tag="Reading lines in file...", end_tag="Line Count Time")
    print("Lines in file: {}".format(lc))
    values = np.zeros((lc+1))
    start_time = time.time_ns()
    if args.verbose:
        print("Starting parsing input...")
    with open(filepath) as f:
        line_fraction = int(math.ceil(lc / 1E2))
        counter = 0
        time_now = 0
        for i, line in enumerate(f):
            log = re.split(", ", line) 
            # divide by 1000 to go from nsec -> usec, KiB/sec -> MiB/sec or IOPS -> kIOPS 
            values[i] = int(log[1]) / 1000
            if(counter % line_fraction == 0):
                time_now = time.time_ns()
                print("Progress: {:.0f}% ({:.3f} msec)".format(((counter / lc) * 100), (time_now - start_time) / 1E6),end="\r")
                start_time = time_now
            counter += 1
    print()
    if args.verbose:
        print("Finished parsing input. Building graph(s)...")
    return values

def histogram(args, sample, smin, smax):
    fig, ax = plt.subplots()
    ax.hist(sample,bins=args.bins, density=True, stacked=True, log=args.ylog, range=(smin, smax))
    ax.set(xlabel=args.xlabel, ylabel="Propability density",title="Distribution of measurements")
    if(args.windowed):
        plt.show()
    else:
        plt.savefig(args.output)
    plt.close()
    
def normal_distribution(args, sample, smin, smax): 
    if (args.verbose): # calculate parameters
        print("Calculate parameters...")
    sample_mean = np.mean(sample)
    sample_std = np.std(sample)
    print('Mean=%.3f, Standard Deviation=%.3f' % (sample_mean, sample_std))

    if (args.verbose): # define the distribution
        print("Define the distribution...")
    dist = norm(sample_mean, sample_std)

    if (args.verbose): # sample probabilities for a range of outcomes
        print("Sample probabilities for a range of outcomes...")
    values = [value for value in range(int(smin), int(smax))]
    probabilities = [dist.pdf(value) for value in values]
    
    if (args.verbose): # plot the histogram and pdf
        print("Plot the histogram and pdf...")
    fig, ax = plt.subplots()
    ax.hist(sample, bins=args.bins, density=True, stacked=True, log=args.ylog, range=(smin, smax))
    ax.plot(values, probabilities)
    ax.set(xlabel=args.xlabel, ylabel="Propability density",title="Distribution of measurements")
    if(args.windowed):
        plt.show()
    else:
        plt.savefig(args.output)
    plt.close()

def calc_density(args, sample, smin, smax):
    """
    Train a Kernel Density Estimation model using sample data and produce probabilities in appropriate range
    """
    if (args.verbose):
        print("Training kernel density model...")
     # training kernel density model
    start_time = time.time_ns()
    model = KernelDensity(bandwidth=args.kbw, kernel=args.kmode)
    sample = sample.reshape((len(sample), 1))
    model.fit(sample)
    if (args.verbose):
        print("Total training time: {:.3f} sec".format((time.time_ns() - start_time) / 1E9))
        print("Sampling probabilities for a range of outcomes...")
        start_time = time.time_ns()
    # sample probabilities for a range of outcomes
    values = np.asarray([value for value in range(int(smin), int(smax))])
    values = values.reshape((len(values), 1))
    probabilities = model.score_samples(values)
    probabilities = np.exp(probabilities)
    if (args.verbose):
        print("Total sampling time: {:.3f} sec".format((time.time_ns() - start_time) / 1E9))
    return (values, probabilities)

def kernel_density(args, sample, smin, smax):
    """
    Processes input using Kernel Density Estimation and plots the pdf (propability density function) along with the histogram
    """
    (values, probabilities) = time_it(calc_density, args.verbose, args, sample, smin, smax, start_tag="", end_tag="Kernel density estimation time")
    
    if (args.verbose): # plotting histogram and pdf
        print("Plotting histogram and pdf...")
    fig, ax = plt.subplots()
    ax.hist(sample, bins=args.bins, density=True, stacked=True, log=args.ylog, range=(smin, smax))
    ax.plot(values[:], probabilities, label=args.kmode)
    ax.set(xlabel=args.xlabel, ylabel="Propability density",title="Kernel Density Estimation")
    ax.legend()
    if(args.windowed):
        plt.show()
    else:
        plt.savefig(args.output)
    plt.close()

def run(args):
    # load and parse input
    sample = load(args, args.filepath)
    if (args.verbose):
        print("File '{}' has been loaded".format(args.filepath))
    
    # calculate min and max values of sample data
    sample_min = np.min(sample)
    sample_max = np.max(sample)
    if (args.verbose):
        print("Min value: {}, Max value: {}".format(sample_min, sample_max))

    # process sample depending on mode
    if(args.mode == "normal"):
        normal_distribution(args, sample, sample_min, sample_max)
    elif(args.mode == "kernel"):
        kernel_density(args, sample, sample_min, sample_max)
    else:
        histogram(args,sample, sample_min, sample_max)

def main():
    parser = argparse.ArgumentParser()
    # required arguments
    parser.add_argument('-f','--filepath', help='absolute/relative filepaths for file to parse', required=True)
    parser.add_argument('-m','--mode', help="histogram mode used for parsing and building graphs", 
                        choices=["simple","normal", "kernel"], required=True)
    # optional arguments
    parser.add_argument('-v','--verbose', help="print more information while running script", default=False, action='store_true')
    parser.add_argument('-w','--windowed', help="instead of writing to file then show in window", default=False, action='store_true')
    parser.add_argument('-o','--output', help="filepath for the built graph. defaults to 'output-hist.png'", default="output-hist.png")
    parser.add_argument('--xlabel', help="label for x-axis. defaults to 'Latency (usec)'", default="Latency (usec)")
    parser.add_argument('--kmode', help="decide what kernel density estimation method to use. defaults to 'gaussian'", 
                        choices=["gaussian", "tophat", "epanechnikov"], default="gaussian")
    parser.add_argument('--kbw', help="set kernel bandwidth, see: https://en.wikipedia.org/wiki/Kernel_density_estimation#Bandwidth_selection. defaults to '0.1'", default=0.1, type=float)
    parser.add_argument('--bins', help="number of bins to distribute values into. defaults to 100.", default=100)
    parser.add_argument('--ylog', help="use a logarithmic y-axis", default=False, action='store_true')

    # prints introduction and measure runtime
    args = parser.parse_args()
    print("Welcome to FioLogParser - Histograms!")
    print("Building graph '{}' in mode '{}' from '{}'".format(args.output, args.mode, args.filepath))
    start_time = time.time_ns()
    run(args)
    print("Completed turning log file(s) into graph ({:.3f} sec).".format((time.time_ns() - start_time) / 1E9))

if __name__ == '__main__':
    main()