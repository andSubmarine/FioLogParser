import re
import time
import argparse
import math

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import colors
from matplotlib.ticker import PercentFormatter
from scipy.stats import norm
from sklearn.neighbors import KernelDensity
from sklearn.model_selection import GridSearchCV, LeaveOneOut

from line_count import line_count
from fio_utils import time_it

def filter_where(arr, k):
    return arr[np.where(arr < k)]

def load(args): 
    lc = time_it(line_count, args.verbose, args.filepath, start_tag="Reading lines in file...", end_tag="Line Count Time")
    print("Lines in file: {}".format(lc))
    load_limit = 1.0 if args.load_limit < 0.0 or args.load_limit > 1.0 else args.load_limit
    N = int((lc+1) * load_limit)
    if args.load_limit:
        print("Loading {} samples...".format(N))
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

def determine_ylabel(args):
    if args.hist_mode == "pdf":
        return "Probability density"
    elif args.hist_mode == "cdf":
        return "Cumulative density"
    else:
        return "Samples Per Bin"

def hist(ax, args, sample, smin, smax):
    '''
    Builds a simple histogram to represent the sample distribution. Typically used to represent the probability density function (pdf) or 
    cumulative density function (cdf) as is.
    '''
    b = int(args.bins) if not args.xlog else 10 ** np.linspace(np.log10(smin), np.log10(smax), int(args.bins))
    if args.hist_mode == "cdf":
        return ax.hist(sample, bins=b, density=True, cumulative=True, log=args.ylog, range=(smin, smax)) 
    elif args.hist_mode == "pdf":
        if args.mode == "simple":
            weights = np.ones_like(sample)/float(len(sample))
            return ax.hist(sample, bins=b, weights=weights, log=args.ylog, range=(smin, smax)) 
        else:
            return ax.hist(sample, bins=b, density=True, log=args.ylog, range=(smin, smax)) 
    else: 
        return ax.hist(sample, bins=b, log=args.ylog, range=(smin, smax)) 

def histogram(args, sample, smin, smax):
    '''
    The simple mode will focus on representing the sample just as a histogram in order to summarize the density.
    '''
    fig, ax = plt.subplots()
    N, bins, patches = hist(ax, args, sample, smin, smax)
    if (args.color):
        color_hist(ax, N, bins, patches)
    ax.set(xlabel=args.xlabel, ylabel=determine_ylabel(args),title="Distribution of measurement values")
    if args.min:
        ax.set_xlim(left=int(args.min))
    if not args.ylog: 
        ax.set_ylim(bottom=0)
    if (args.percentage):
        ax.yaxis.set_major_formatter(PercentFormatter(xmax=1,decimals=3))
    
def normal_distribution(args, sample, smin, smax): 
    '''
    Assumes that the sample shows a common distribution which only involve two parameters: mean and standard deviation.
    This mode will estimate these parameters from the sample data and plot the resulting normal distribution onto the histogram.
    '''
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
    N, bins, patches = hist(ax, args, sample, smin, smax)
    if (args.color):
        color_hist(ax, N, bins, patches)
    ax.set(xlabel=args.xlabel, ylabel=determine_ylabel(args),title="Parametric Density Estimation")
    if (args.percentage):
        ax.yaxis.set_major_formatter(PercentFormatter(xmax=1,decimals=3))
    ax.plot(values, probabilities)
    if args.show_means:
        plt.axvline(x=sample_mean, label="mean", c="b")
        plt.axvline(x=sample_mean+sample_std, label="mean+std", c="g", linestyle="dotted")
        plt.axvline(x=sample_mean-sample_std, label="mean-std", c="r", linestyle="dashed")
        plt.legend()
    if args.min:
        ax.set_xlim(left=int(args.min))
    if not args.ylog: 
        ax.set_ylim(bottom=0)

def determine_bandwidth(args, train):
    '''
    Determines the bandwidth for kernel density estimation. 
    
    Note: Kernel bandwidth has nothing to do with the metric bandwidth of fio log files. 
    Instead the kernel bandwidth specifies the size of the kernel at each point and thus how *smooth* the kernel will become.
    '''
    # determine optimal bandwidth based on training dataset
    if (args.verbose):
        print("Determining optimal bandwidth...")
    start_time = time.time_ns()
    bandwidths = np.linspace(0.0, 5.0, 100, dtype=float)
    grid = GridSearchCV(KernelDensity(kernel=args.kmode, atol=args.absolute_tolerance, rtol=args.relative_tolerance),
                        {'bandwidth': bandwidths})
    train = train.reshape((len(train), 1))
    grid.fit(train)
    end_time = time.time_ns()
    print("Found optimal bandwidth in {:.3f} sec".format((end_time - start_time) / 1E9))
    print("Optimal bandwidth: {}".format(grid.best_params_.bandwidth))
    return grid.best_params_.bandwidth

def split(args, sample):
    '''
    Splits the data sample into training (used for bandwidth determination) and validation (trains model) datasets.
    See also '--training_split' for more information.
    '''
    if (args.verbose):
        print("Splitting dataset into training and test datasets...")
    if not args.kernel_bandwidth and args.training_split:
        train, validate = np.split(sample, [int(len(sample)*args.training_split), int(len(sample)*1)])
        print("Train dataset: {} samples ({}%), ".format(len(train), args.training_split * 100))        
        print("Validation dataset: {} samples ({}%), ".format(len(validate), (1-args.training_split) * 100))
        return (train, validate)
    else:
        validate, test = np.array_split(sample, 2)  
        print("Validation dataset: {} samples ({}%), ".format(len(validate), 100))
        return (np.empty((1,0)), sample)

def calc_density(args, sample, smin, smax):
    """
    Train a Kernel Density Estimation model using sample data and produce probabilities in appropriate range
    """
    # split dataset into training, validation and test datasets
    train, validate = split(args, sample)
    start_time = time.time_ns()
    bw = float(args.kernel_bandwidth) if args.kernel_bandwidth else determine_bandwidth(args, train)
    # training kernel density model
    if (args.verbose):
        print("Training kernel density model...")
    validate = validate.reshape((len(validate), 1))
    model = KernelDensity(bandwidth=args.kernel_bandwidth, kernel=args.kmode, atol=args.absolute_tolerance, rtol=args.relative_tolerance)
    model = model.fit(validate)
    print("Total training time: {:.3f} sec".format((time.time_ns() - start_time) / 1E9))
    if (args.verbose):
        print("Sampling probabilities for a range of outcomes...")
    start_time = time.time_ns()
    # sample probabilities for a range of outcomes
    test = np.linspace(smin, smax, 100, dtype=float)
    test = test.reshape((len(test), 1))
    print("Total log probability density score: {}".format(model.score(test)))
    print("Scoring time: {:.3f} sec".format((time.time_ns() - start_time) / 1E9))
    t = time.time_ns()
    probabilities = model.score_samples(test)
    print("Evaluation time: {:.3f} sec".format((time.time_ns() - t) / 1E9))
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
    N, bins, patches = hist(ax, args, sample, smin, smax)
    if (args.color):
        color_hist(ax, N, bins, patches)
    if (args.percentage):
        ax.yaxis.set_major_formatter(PercentFormatter(xmax=1,decimals=3))
    ax.plot(values[:], probabilities, label=args.kmode)
    ax.set(xlabel=args.xlabel, ylabel=determine_ylabel(args),title="Kernel Density Estimation")
    if args.min:
        ax.set_xlim(left=int(args.min))
    if not args.ylog: 
        ax.set_ylim(bottom=0)
    ax.legend()

def run(args):
    '''
    The regular runtime flow is outlined as follows:
    1. load and parse input
    2. calculate min and max values in data sample to specify range
    3. process sample depending on mode, see '-m' or '--mode' in argument list for more infomation regarding these
    4. output temporal measurements of execution
    5. output results either directly to file or in a new window 
    '''
    start_time = time.time_ns()
    # load and parse input
    sample = time_it(load,args.verbose, args, end_tag="File loading time")
    
    # calculate min and max values of sample data
    sample_min = int(args.min) if args.min else np.min(sample)
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
        
    print("Completed turning log file(s) into graph ({:.3f} sec).".format((time.time_ns() - start_time) / 1E9))
    if(args.windowed):
        plt.show()
    else:
        plt.savefig(args.output)
    plt.close()

def main():
    '''
    The main function handles specifying how the program can be executed including which arguments are required and optional for running the program. 
    See below for a full list or use '-h' or '--help' for more information about each argument.
    '''
    parser = argparse.ArgumentParser()
    # required arguments
    parser.add_argument('-f','--filepath', help='absolute/relative filepaths for file to parse', required=True)
    parser.add_argument('-m','--mode', help="histogram mode used for parsing and building graphs", 
                        choices=["simple","normal", "kernel"], required=True)

    # optional arguments - general
    parser.add_argument('-v','--verbose', help="print more information while running script", default=False, action='store_true')

    parser.add_argument('-w','--windowed', help="instead of writing to file then show in window", default=False, action='store_true')
    parser.add_argument('-o','--output', help="filepath for the built graph. defaults to 'output-hist.png'", default="output-hist.png")
    
    parser.add_argument('-hm', '--hist_mode', help="select a mode for how the histogram should represent probability density. defaults to 'pdf'", default="pdf", choices=["pdf","cdf","val"])

    # optional arguments - limits
    parser.add_argument('--bins', help="number of bins to distribute values into. defaults to 100.", default=100)
    parser.add_argument('--min', help="specify minimum data value for range")
    parser.add_argument('--max', help="specify maximum data value for range.")
    parser.add_argument('-c','--outlier_cutoff', help="specify a maximum value so only a range (0-value) of measurements are processed further.")
    parser.add_argument('-ll','--load_limit', help="limits the amount of data to be loaded in for processing. provide as decimal percentage. defaults to 1.", default=1.0, type=float)
    
    # optional arguments - normal mode
    parser.add_argument('--show_means', help="in 'normal' mode then show the calculated mean and standard deviation on generated graph", default=False, action='store_true')

    # optional arguments - kernel mode
    parser.add_argument('--training_split', help="how large a fraction that the training data should be out of total dataset. defaults to 0.5, i.e. 50%", default=0.5, type=float)
    parser.add_argument('-kbw', '--kernel_bandwidth', help="set kernel bandwidth. note that setting this value has the consequence that training dataset is ignored.", type=float)
    parser.add_argument('--kmode', help="decide what kernel density estimation method to use. defaults to 'gaussian'", 
                        choices=["gaussian", "tophat", "epanechnikov"], default="gaussian")
    parser.add_argument('-atol','--absolute_tolerance', help="specify the absolute tolerance for kernel estimation. defaults to '0.0'", default=0.0, type=float)
    parser.add_argument('-rtol','--relative_tolerance', help="specify the relative tolerance for kernel estimation. defaults to '0.0'", default=0.0, type=float)

    # optional arguments - visuals
    parser.add_argument('--xlabel', help="label for x-axis. defaults to 'Latency (usec)'", default="Latency (usec)")
    parser.add_argument('--ylog', help="use a logarithmic y-axis. disabled by default.", default=False, action='store_true')
    parser.add_argument('--xlog', help="use a logarithmic x-axis. disabled by default.", default=False, action='store_true')
    parser.add_argument('--color', help="color the histogram according to height. disabled by default.", default=False, action='store_true')
    parser.add_argument('--percentage', help="represent probability density by percentage instead of decimal. disabled by default.", default=False, action='store_true')

    # prints introduction and measure runtime
    args = parser.parse_args()
    print("Welcome to FioLogParser - Histograms!")
    print("Building graph '{}' in mode '{}' from '{}'".format(args.output, args.mode, args.filepath))
    run(args)

if __name__ == '__main__':
    main()