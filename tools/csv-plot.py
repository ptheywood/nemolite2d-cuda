#! /usr/bin/python3

"""
Python3 script for plotting (one or more) CSVs using matplotlib. 

"""

import os
import sys
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from collections import OrderedDict
import seaborn as sns

EXIT_FAILURE = 1
EXIT_SUCCESS = 0

CSV_EXT=".csv"

# Define command line arguments for this application
def cli_args():
    # Get arguments using argparse
    parser = argparse.ArgumentParser(
        description="Extract benchmark data from nemo2d stdout logs"
        )
    parser.add_argument(
        "files",
        type=str,
        nargs="+",
        help="csv files to parse."
        )

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="location for output file"
    )
    parser.add_argument(
        "-s",
        "--show",
        action="store_true",
        help="show the graph."
    )
    parser.add_argument(
        "--logy",
        action="store_true",
        help="log scale for y axis."
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="force overwriting of --output file."
      )


    args = parser.parse_args()
    return args

# Validate command line arguments for pre-empative abortion.
def validate_args(args):
    # Build the list of log files to be parsed.
    valid_files = []
    if args.files is not None and len(args.files) > 0:
        for file_or_path in args.files:
            if os.path.isfile(file_or_path) and file_or_path.endswith(CSV_EXT):
                valid_files.append(file_or_path)
            elif os.path.isdir(file_or_path):
                for root, dirs, files in os.walk(file_or_path):
                    for file in files:
                        if file.endswith(CSV_EXT):
                            valid_files.append(os.path.join(root, file))
            else:
                print("Warning: Provided file {:} does not exist".format(file_or_path))
    # Remove duplicates from valid files and sort
    valid_files = sorted(list(set(valid_files)))

    if valid_files is None or len(valid_files) == 0:
        print("Error: No valid files provided.")
        return False, None
    # Check use of --output and --force
    if args.output is not None:
        # @todo - potential disk race by checking this upfront. Should use try catch later too.
        if os.path.exists(args.output):
            if os.path.isdir(args.output):
                print("Error: {:} is a directory".format(args.sample))
                return False, None
            elif os.path.isfile(args.output):
                if not args.force:
                    print("Error: Output file {:} already exists. Please use -f/--force")
                    return False, None

    return True, valid_files

def parse_files(files):
    # Load each file into a data frame. 
    dfs = {}
    for index, file in enumerate(files):
        df = pd.read_csv(file)
        dfs[file] = df

    # Combine dataframes
    combined = pd.concat(dfs.values())
    return combined

def plot(data, args):
    # Get the columns 
    columns = list(data.columns)

    # Get the builds.
    if "build" not in columns:
        print("Error: build column missing!")
        return False 
    builds = list(data["build"].unique())

    # Get the Scales 
    if "scale" not in columns:
        print("Error: scale column missing!")
        return False
    scales = list(data["scale"].unique())

    # Select a column to plot
    

    ycols = [
        # "build",
        # "scale",
        "time_stepping_total",
        # "time_stepping_average",
        # "continuity_total",
        # "continuity_average",
        "momentum_total",
        # "momentum_average",
        # "bcs_total",
        # "bcs_average",
        # "next_total",
        # "next_average",
    ]

    valid_ycols = []
    for ycol in ycols:
        if ycol not in columns:
            print("Warning, selected column {:} not present".format(ycol))
        else:
            valid_ycols.append(ycol)

    ycols = valid_ycols
    if len(ycol) == 0:    
        print("Warning, setting default ycol")
        ycols = [columns[2]]

    # Plot the data
    sns.set(style="darkgrid")

    markers = ["o", "s", "P", "^", "6", "X" ] 
    linestyles=["-", "--", ":"]

    fig, ax = plt.subplots(figsize=(16,9))
    for bindex, build in enumerate(builds):
        palette = sns.color_palette("husl", len(ycols))
        # palette = sns.cubehelix_palette(len(ycols), start=bindex, dark=0.5, light=0.8, reverse=True)

        linestyle = linestyles[bindex % len(linestyles)]
        qdata = data.query("build == '{:}'".format(build))

        for yindex, ycol in enumerate(ycols):
            sindex = bindex * len(builds) + yindex
            marker = markers[sindex % len(markers)]
            colour = palette[yindex % len(ycols)]
            label="{:} {:}".format(build, ycol)
            ax.plot(qdata["scale"], qdata[ycol], marker=marker, linestyle=linestyle, color=colour, label=label)

    plt.legend(loc='upper left')
    plt.xlabel("scale")
    plt.ylabel("time(seconds)")
    plt.xscale("linear")
    if args.logy:
        plt.yscale("log", basey=10)

    # Save to disk?
    if args.output is not None and (not os.path.exists(args.output) or args.force):
        plt.savefig(args.output, dpi=150) 
        print("Figure saved to {:}".format(args.output))

    # Show on the screen?
    if args.output is None or args.show == True:
        plt.show()

    return True

def main():
    # parse command line args
    args = cli_args()
    # Validate input, building the list of files to be parsed. 
    valid, files = validate_args(args)
    if not valid:
        return False

    # Parse the files
    data = parse_files(files)

    # Plot the data
    plotted = plot(data, args)

    # Return the success of the function. True == success. 
    return plotted


if __name__ == "__main__":
    # Exit with an appropriate errorcode.
    success = main()
    if success:
        exit(EXIT_SUCCESS)
    else:
        exit(EXIT_FAILURE)