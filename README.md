# FioLogParser
The purpose of FioLogParser and its associated scripts is to enable parsing and processing of log files generated by Fio during experiments. For general uses, you can use scripts found in `/examples` such as `graph-ios-builder.sh` or `graph-io_count-builder.sh` to quickly generate graphs based on log files. 

This repository and the associated set of tools were built by Andreas Blanke ([@andSubmarine](https://github.com/andSubmarine)) and Magnus Krøyer ([@MackAtITU](https://github.com/MackatITU)) as part of their Master Thesis at the IT-University of Copenhagen (ITU).

## Setup
Run the following to setup the required packages to run FioLogParser and associated scripts. Please be aware that the command should be run with administrive rights (Run as Administrator on Windows or with `sudo` on Linux):

```
pip install -r requirements.txt
```

## FioLogParser
### Quick Start
The purpose of FioLogParser is to provide a general-purpose interface to scripts such as `fioelapsed.py` which generate different kinds of graphs based on Fio log files. 

If you want to get started quickly with parsing a log file and building a graph then you can use the following command in the `/src` folder:

```
python fiologparser -m ios -lt bw -f test_bw.1.log
```

The first required argument `-m` or `--mode` can either be `ios`, `io_count` or `elapsed` and determines the mode for parsing and building the graph. 

In the `ios` mode, measurement values are plotted per I/O request as they appear in the log file. That means that the y-axis represents measurement values while the x-axis represent the order of I/O's being submitted and completed. 

In `io_count` mode, measurement values are not as such important and instead the frequency of IOs is measured by the standard metric called IOPS or Input / Outputs Per Second. This is done by examining and using the log file's timestamps and counting the amount of I/Os that occured over a period of time which is typically one second. The IOPS value is then plotted on the y-axis of the graph while the x-axis is used to show IOPS values change over time.

In `elapsed` mode then a average over a number of log entries is computed (can also be configured such that the log time is used for determining the average window). 

The second required argument `-lt` or `--log-type` can either be `bw`, `lat` or `iops` and **indicates the metric used by Fio in the log file**. If you're in doubt about the log type then remember that `fio` typically uses a naming convention such as `<jobname>_<logtype>.<jobnumber>.log` so you can inspect the name of the file that you want to parse and find the logtype.

The third required argument `-f` or `--files` should be used with a list of filepaths for the files that `fiologparser` should parse. 

### Advanced Usage
The following can also be produced by running `fiologparser.py` with the `-h` or `--help` flag. 

```
$> python fiologparser.py -h
Welcome to FioLogParser!
usage: fiologparser.py [-h] -m {elapsed,ios,io_count} -lt {bw,lat,iops} -f FILES [FILES ...] [-o OUTPUT] [--title TITLE] [-v] [--every_nth EVERY_NTH] [--same_time] [-ylog]  
                       [-agg] [-gt {default,bar,line,dots,errorbar}]

optional arguments:
  -h, --help            show this help message and exit
  -m {elapsed,ios,io_count}, --mode {elapsed,ios,io_count}
                        the mode used for parsing and building graphs
  -lt {bw,lat,iops}, --logtype {bw,lat,iops}
                        the type for values in files
  -f FILES [FILES ...], --files FILES [FILES ...]
                        absolute/relative filepaths for files to parse
  -o OUTPUT, --output OUTPUT
                        filepath for the built graph. defaults to 'output.png'
  --title TITLE         the title of the built graph
  -v, --verbose         print more information while running script
  --every_nth EVERY_NTH
                        iterate over n values. used for mode 'elapsed' and 'io_count'. defaults to 1
  --same_time           specify that iterations should occur based on time
  -ylog, --logscale_y   use a logirithm scale instead of a linear scale for the y-axis
  -agg, --aggregate_files
                        aggregate results from multiple logs into a single data set
  -gt {default,bar,line,dots,errorbar}, --graphtype {default,bar,line,dots,errorbar}
                        the type of graph to be built. defaults to a mode-specific default
```
