# FioLogParser
Within this folder there exists a number of scripts to help enable parsing fio log files and building graphs based on parsed data.

The main script for this is the `fiologparser.py` which parses one or more log files of the same type and builds a graph using the given mode. Other scripts include `line_count.py` which requires a `filepath` and then outputs the number of lines found in the file. `fiologparser` uses `line_count` in order to estimate how much data needs to be parsed.

## Quick-Start
If you want to get started quickly with parsing a log file and building a graph then you can use the following command:

```
python3 fiologparser -m ios -lt bw -f test_bw.1.log
```

The first required argument `-m` or `--mode` can either be `ios` or `elapsed` and determines the mode for parsing and building the graph. In `ios` mode then every value in the file(s) is extracted and placed on the x-axis in order of line number ascendingly. In `elapsed` mode then a average over a number of log entries is computed (can also be configured such that the log time is used for determining the average window). 

The second required argument `-lt` or `--log-type` can either be `bw`, `lat` or `iops` and specifies how values in the log file should be interpreted. If you're in doubt about the log type then remember that `fio` typically uses a naming convention such as `<jobname>_<logtype>.<jobnumber>.log` so you can inspect the name of the file that you want to parse and find the logtype.

The third required argument `-f` or `--files` should be used with a list of filepaths for the files that `fiologparser` should parse. 

## Usage
The following can also be produced by running `fiologparser-py` with the `-h` or `--help` flag. 

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
