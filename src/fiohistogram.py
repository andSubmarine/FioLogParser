import re
import time
import argparse
import math

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from scipy.stats import norm
from sklearn.neighbors import KernelDensity
from sklearn.model_selection import GridSearchCV, LeaveOneOut

from line_count import line_count
from fio_utils import time_it
from matplotlib import colors
from matplotlib.ticker import PercentFormatter

def filter_where(arr, k):
    return arr[np.where(arr < k)]

def load(args): 
    lc = time_it(line_count, args.verbose, args.filepath, start_tag="Reading lines in file...", end_tag="Line Count Time")
    print("Lines in file: {}".format(lc))
    limit = 1.0 if args.limit < 0.0 or args.limit > 1.0 else args.limit
    N = int((lc+1) * limit)
    values = np.zeros(N)
    start_time = time.time_ns()
    if args.verbose:
        print("Starting parsing input...")
    with open(args.filepath) as f:
        line_fraction = int(math.ceil(lc / 1E2))
        counter = 0
        time_now = 0
        for i, line in enumerate(f):
            if i == N:
                break
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
    if args.outlier_cutoff:
        prev_length = len(values)
        values = filter_where(values, int(args.outlier_cutoff))
        print("Reduced dataset by {} with upper cutoff at {}".format(prev_length-len(values),args.outlier_cutoff))
    return values

def color_hist(ax, N, bins, patches): 
    fracs = N / N.max()
    norm = colors.Normalize(fracs.min(), fracs.max())
    for thisfrac, thispatch in zip(fracs, patches):
        color = plt.cm.viridis(norm(thisfrac))
        thispatch.set_facecolor(color)

def histogram(args, sample, smin, smax):
    fig, ax = plt.subplots()
    b = int(args.bins) if not args.xlog else 10 ** np.linspace(np.log10(smin), np.log10(smax), int(args.bins))
    useDensity = args.hist_mode != "val" # If True, draw and return a probability density: each bin will display the bin's raw count divided by the total number of counts and the bin width, so that the area under the histogram integrates to 1
    useCumulative = args.hist_mode == "cdf" # If True, then a histogram is computed where each bin gives the counts in that bin plus all bins for smaller values. The last bin gives the total number of datapoints which is normalized to 1 due to density
    # useStacked = args.hist_mode == "pdf" # If True and Density is True, then the sum of the histograms is normalized to 1.
    N, bins, patches = ax.hist(sample, bins=b, density=useDensity, cumulative=useCumulative, log=args.ylog, range=(smin, smax))
    if (args.color):
        color_hist(ax, N, bins, patches)
    ax.set(xlabel=args.xlabel, ylabel="Propability density",title="Distribution of measurement values")
    if args.min:
        ax.set_xlim(left=int(args.min))
    if not args.ylog: 
        ax.set_ylim(bottom=0)
    if (args.percentage):
        ax.yaxis.set_major_formatter(PercentFormatter(xmax=1,decimals=3))
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
    b = int(args.bins) if not args.xlog else 10 ** np.linspace(np.log10(smin), np.log10(smax), int(args.bins))
    useDensity = args.hist_mode != "val" # If True, draw and return a probability density: each bin will display the bin's raw count divided by the total number of counts and the bin width, so that the area under the histogram integrates to 1
    useCumulative = args.hist_mode == "cdf" # If True, then a histogram is computed where each bin gives the counts in that bin plus all bins for smaller values. The last bin gives the total number of datapoints which is normalized to 1 due to density
    # useStacked = args.hist_mode == "pdf" # If True and Density is True, then the sum of the histograms is normalized to 1.
    N, bins, patches = ax.hist(sample, bins=b, density=useDensity, cumulative=useCumulative, log=args.ylog, range=(smin, smax))
    if (args.color):
        color_hist(ax, N, bins, patches)
    ax.set(xlabel=args.xlabel, ylabel="Propability density",title="Parametric Density Estimation")
    if (args.percentage):
        ax.yaxis.set_major_formatter(PercentFormatter(xmax=1,decimals=3))
    ax.plot(values, probabilities)
    if args.min:
        ax.set_xlim(left=int(args.min))
    if not args.ylog: 
        ax.set_ylim(bottom=0)
    if(args.windowed):
        plt.show()
    else:
        plt.savefig(args.output)
    plt.close()

def determine_bandwidth(args, train):
    # determine optimal bandwidth based on training dataset
    if (args.verbose):
        print("Determining optimal bandwidth...")
    start_time = time.time_ns()
    bandwidths = np.linspace(0.0, 5.0, 100, dtype=float)
    grid = GridSearchCV(KernelDensity(kernel='gaussian'),
                        {'bandwidth': bandwidths})
    train = train.reshape((len(train), 1))
    grid.fit(train)
    end_time = time.time_ns()
    print("Found optimal bandwidth in {:.3f} sec".format((end_time - start_time) / 1E9))
    print("Optimal bandwidth: {}".format(grid.best_params_.bandwidth))
    return grid.best_params_.bandwidth

def calc_density(args, sample, smin, smax):
    """
    Train a Kernel Density Estimation model using sample data and produce probabilities in appropriate range
    """
    # split dataset into training, validation and test datasets
    if (args.verbose):
        print("Splitting dataset into training, validation and test datasets...")
    train, validate, test = np.split(sample, [int(len(sample)*args.training_split), int(len(sample)*(1.0-args.training_split))])
    start_time = time.time_ns()
    bw = float(args.kbw) if args.kbw else determine_bandwidth(args, train)
    # training kernel density model
    if (args.verbose):
        print("Training kernel density model...")
    validate = validate.reshape((len(validate), 1))
    model = KernelDensity(bandwidth=args.kbw, kernel=args.kmode)
    model = model.fit(validate)
    if (args.verbose):
        print("Sampling probabilities for a range of outcomes...")
    print("Total training time: {:.3f} sec".format((time.time_ns() - start_time) / 1E9))
    start_time = time.time_ns()
    # sample probabilities for a range of outcomes
    test = test.reshape((len(test), 1))
    probabilities = model.score_samples(test)
    probabilities = np.exp(probabilities)
    print("Total sampling time: {:.3f} sec".format((time.time_ns() - start_time) / 1E9))
    return (test, probabilities)

def kernel_density(args, sample, smin, smax):
    """
    Processes input using Kernel Density Estimation and plots the pdf (propability density function) along with the histogram
    """
    (values, probabilities) = time_it(calc_density, args.verbose, args, sample, smin, smax, start_tag="", end_tag="Kernel density estimation time")
    
    if (args.verbose): # plotting histogram and pdf
        print("Plotting histogram and pdf...")
    fig, ax = plt.subplots()
    b = int(args.bins) if not args.xlog else 10 ** np.linspace(np.log10(smin), np.log10(smax), int(args.bins))
    useDensity = args.hist_mode != "val" # If True, draw and return a probability density: each bin will display the bin's raw count divided by the total number of counts and the bin width, so that the area under the histogram integrates to 1
    useCumulative = args.hist_mode == "cdf" # If True, then a histogram is computed where each bin gives the counts in that bin plus all bins for smaller values. The last bin gives the total number of datapoints which is normalized to 1 due to density
    # useStacked = args.hist_mode == "pdf" # If True and Density is True, then the sum of the histograms is normalized to 1.
    N, bins, patches = ax.hist(sample, bins=b, density=useDensity, cumulative=useCumulative, log=args.ylog, range=(smin, smax))
    if (args.color):
        color_hist(ax, N, bins, patches)
    if (args.percentage):
        ax.yaxis.set_major_formatter(PercentFormatter(xmax=1,decimals=3))
    ax.plot(values[:], probabilities, label=args.kmode)
    ax.set(xlabel=args.xlabel, ylabel="Propability density",title="Kernel Density Estimation")
    if args.min:
        ax.set_xlim(left=int(args.min))
    if not args.ylog: 
        ax.set_ylim(bottom=0)
    ax.legend()
    if(args.windowed):
        plt.show()
    else:
        plt.savefig(args.output)
    plt.close()

def run(args):
    # load and parse input
    sample = load(args)
    if (args.verbose):
        print("File '{}' has been loaded".format(args.filepath))
    
    # calculate min and max values of sample data
    sample_min = np.min(sample) if not args.min else int(args.min)
    sample_max = int(args.max) if args.max and not args.outlier_cutoff else np.max(sample) if not args.outlier_cutoff else int(args.outlier_cutoff)
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
    parser.add_argument('-l','--limit', help="limits the amount of data to be loaded into the graph. provide as decimal percentage. defaults to 1.", default=1.0, type=float)
    parser.add_argument('--xlabel', help="label for x-axis. defaults to 'Latency (usec)'", default="Latency (usec)")
    parser.add_argument('--kmode', help="decide what kernel density estimation method to use. defaults to 'gaussian'", 
                        choices=["gaussian", "tophat", "epanechnikov"], default="gaussian")
    parser.add_argument('--bins', help="number of bins to distribute values into. defaults to 100.", default=100)
    parser.add_argument('--outlier_cutoff', help="specify a maximum value so only a range (0-value) of measurements are processed further.")
    parser.add_argument('--min', help="specify minimum data value for range")
    parser.add_argument('--max', help="specify maximum data value for range.")
    parser.add_argument('--ylog', help="use a logarithmic y-axis. disabled by default.", default=False, action='store_true')
    parser.add_argument('--xlog', help="use a logarithmic x-axis. disabled by default.", default=False, action='store_true')
    parser.add_argument('--color', help="color the histogram according to height. disabled by default.", default=False, action='store_true')
    parser.add_argument('--percentage', help="represent probability density by percentage instead of decimal. disabled by default.", default=False, action='store_true')
    parser.add_argument('-hm', '--hist_mode', help="select a mode for how the histogram should represent probability density. defaults to 'pdf'", default="pdf", choices=["pdf","cdf","val"])
    parser.add_argument('--training_split', help="how large a fraction that the training data should be out of total dataset. defaults to 0.5, i.e. 50%", default=0.5, type=float)
    parser.add_argument('--kbw', help="set kernel bandwidth. note that setting this value has the consequence that training dataset is ignored.", type=float)

    # prints introduction and measure runtime
    args = parser.parse_args()
    print("Welcome to FioLogParser - Histograms!")
    print("Building graph '{}' in mode '{}' from '{}'".format(args.output, args.mode, args.filepath))
    start_time = time.time_ns()
    run(args)
    print("Completed turning log file(s) into graph ({:.3f} sec).".format((time.time_ns() - start_time) / 1E9))

if __name__ == '__main__':
    main()