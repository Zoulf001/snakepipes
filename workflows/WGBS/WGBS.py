#!/usr/bin/env python3

__version__ = "0.7.1"
pipev=__version__

__description__ = """
WGBS workflow v{version} - MPI-IE workflow for WGBS analysis

usage example:
    WGBS -ri read_input_dir -w output-dir mm10
""".format(version=__version__)

import argparse
import os
import signal
import subprocess
import sys
import textwrap
import time
import shutil
import yaml
import inspect
import glob
import pandas

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(inspect.getfile(inspect.currentframe()) )))))+"/shared/")
import common_functions as cf

def parse_args(defaults={"verbose":None,"configfile":None,"max_jobs":None,"nthreads":None,"snakemake_options":None,"tempdir":None,
                         "downsample":None, "trimReads":None,"fqcin":None,"nextera":None,"trimThreshold":None,"trimOtherArgs":None,"convrefpath":None,
                         "convRef":None,"intList":None, "blackList":None,"sampleInfo":None,"mbias_ignore":None }):
    """
    Parse arguments from the command line.
    """

    parser = argparse.ArgumentParser(
        prog=sys.argv[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(__description__),
        add_help=False
    )

    ## positional/required
    parser.add_argument("genome",
                        metavar="GENOME",
                        help="Genome acronym of target organism (supported: 'dm3', 'dm6', 'hs37d5', 'mm9', 'mm10', 'SchizoSPombe_ASM294v2')")

    required = parser.add_argument_group('required arguments')
    required.add_argument("-ri", "--indir",
                        dest="indir",
                        help="input directory containing the paired-end FASTQ files",
                        required=True)

    required.add_argument("-w", "--wdir",
                        dest="wdir",
                        help="working directory",
                        required=True)

    general = parser.add_argument_group('general arguments')
    general.add_argument("-h", "--help",
                        action="help",
                        help="show this help message and exit")

    general.add_argument("-v", "--verbose",
                        dest="verbose",
                        action="store_true",
                        help="verbose output (default: '%(default)s')",
                        default=defaults["verbose"])

    general.add_argument("-c", "--configfile",
                        dest="configfile",
                        help="configuration file: config.yaml. In absence of a config file, the default options from the "
                        "workflows would be selected from /workflows/<workflow_name>/defaults.yaml (default: '%(default)s')",
                        default=defaults["configfile"])
   
    general.add_argument("--cluster_configfile",
                        dest="cluster_configfile",
                        help="configuration file for cluster usage. In absence, the default options "
                        "from shared/cluster.yaml and [workflow]/cluster.yaml would be selected (default: '%(default)s')",
                        default=None)

    general.add_argument("-j", "--jobs",
                        dest="max_jobs",
                        metavar="INT",
                        help="maximum number of concurrently submitted Slurm jobs / cores if workflow is run locally (default: '%(default)s')",
                        type=int,
                        default=defaults["max_jobs"])

    general.add_argument("-nt", "--nthreads",
                        dest="nthreads",
                        metavar="INT",
                        help="number of threads to use for multi-threaded tasks",
                        type=int,
                        default=defaults["nthreads"])


    general.add_argument("--local",
                        dest="local",
                        action="store_true",
                        default=False,
                        help="run workflow locally; default: jobs are submitted to Slurm queue (default: '%(default)s')")

    general.add_argument("--snakemake_options",
                        dest="snakemake_options",
                        metavar="STR",
                        type=str,
                        help="Snakemake options to be passed directly to snakemake, e.g. use "
                        "--snakemake_options='--dryrun --rerun-incomplete --unlock --forceall'. (default: '%(default)s')",
                        default=defaults["snakemake_options"])

    general.add_argument("--tempdir",
                        dest="tempdir",
                        type=str,
                        help="used prefix path for temporary directory created via mktemp. Created temp dir gets exported as "
                        "$TMPDIR and is removed at the end of this wrapper! (default: '%(default)s')",
                        default=defaults["tempdir"])

    ## optional
    optional = parser.add_argument_group('optional')

    optional.add_argument("--downsample",
                        dest="downsample",
                        metavar="INT",
                        help="downsample the given number of reads randomly from of each FASTQ file (default: '%(default)s')",
                        type=int,
                        default=defaults["downsample"])

    optional.add_argument("--trimReads",
                        dest="trimReads",
                        action="store",
                        choices=['auto','user',None],
                        help="Activate fastq read trimming. If activated, Illumina adaptors are trimmed by default. "
                        "Additional parameters can be specified under --trimOtherArgs (default: '%(default)s')",
                        default=defaults["trimReads"])

    optional.add_argument("--fqcin",
                        dest="fqcin",
                        action="store",
                        help="Folder with fastqc.zip files to automatically detect hard trimming threshold. ",
                        default=defaults["fqcin"])


    optional.add_argument("--nextera",
                        dest="nextera",
                        action="store",
                        help="Trim nextera adapters rather than TruSeq adapters (default: '%(default)s')",
                        default=defaults["nextera"])

    optional.add_argument("--trimThreshold",
                        dest="trimThreshold",
                        metavar="STR",
                        type=str,
                        help="Trimming threshold for cutadapt. (default: '%(default)s')",
                        default=defaults["trimThreshold"])


    optional.add_argument("--trimOtherArgs",
                        dest="trimOtherArgs",
                        metavar="STR",
                        type=str,
                        help="Additional arguments passed to cutadapt. (default: '%(default)s')",
                        default=defaults["trimOtherArgs"])


    optional.add_argument("--cref",
                        dest="convrefpath",
                        metavar="STR",
                        type=str,
                        help="Path to converted reference genome. (default: '%(default)s')",
                        default=defaults["convrefpath"])

    optional.add_argument("--convRef",
                        dest="convRef",
                        metavar="STR",
                        type=str,
                        help="Convert reference genome. (default: '%(default)s')",
                        default=defaults["convRef"])


    optional.add_argument("--intList",
                        dest="intList",
                        metavar="STR",
                        action='append',
                        help="Bed file(s) with target intervals to run analysis on. Use multiple times to pass multiple bed files. (default: '%(default)s')",
                        default=defaults["intList"])

    optional.add_argument("--blackList",
                        dest="blackList",
                        metavar="STR",
                        action='store',
                        type=str,
                        help="Bed file(s) with SNP positions to mask for methylation calling. (default: '%(default)s')",
                        default=defaults["blackList"])


    optional.add_argument("--sampleInfo",
                        dest="sampleInfo",
                        metavar="STR",
                        action='store',
                        type=str,
                        help="Text file with sample information to use for statistical analysis. (default: '%(default)s')",
                        default=defaults["sampleInfo"])

    optional.add_argument("--mbias",
                        dest="mbias_ignore",
                        metavar="STR",
                        action='store',
                        type=str,
                        help="Number of nucleotides with mbias to ignore during methylation extraction. (default: '%(default)s')",
                        default=defaults["mbias_ignore"])
    


    return parser



def main():
    ## basic paths only used in wrapper
    this_script_dir = os.path.dirname(os.path.realpath(__file__))
    main_dir_path = os.path.join(os.path.dirname(os.path.dirname(this_script_dir)))

    ## defaults
    defaults = cf.load_configfile(os.path.join(this_script_dir, "defaults.yaml"),False)
    ## get command line arguments
    parser = parse_args(defaults)
    args = parser.parse_args()
    args.wdir = os.path.abspath(args.wdir)
    args.cluster_logs_dir = os.path.join(args.wdir, "cluster_logs")

    ## we also add these paths to config, although we dont use them in the Snakefile
    args.this_script_dir = this_script_dir
    args.main_dir_path = main_dir_path

## checks for parameters necessary in wrapper
# 1. Dir path
    if os.path.exists(args.indir):
        args.indir = os.path.abspath(args.indir)
    else:
        print("\nError! Input dir not found! ({})\n".format(args.indir))
        exit(1)
# 2. config file
    if args.configfile and not os.path.exists(args.configfile):
        print("\nError! Provided configfile (-c) not found! ({})\n".format(args.configfile))
        exit(1)

    ## merge configuration dicts
    config = defaults   # 1) form defaults.yaml
    if args.configfile:
        user_config = cf.load_configfile(args.configfile,False)
        config = cf.merge_dicts(config, user_config) # 2) form user_config.yaml
    config_wrap = cf.config_diff(vars(args),defaults) # 3) from wrapper parameters
    config = cf.merge_dicts(config, config_wrap)

    ## Output directory + log directory
    subprocess.call("[ -d {cluster_logs_dir} ] || mkdir -p {cluster_logs_dir}".format(cluster_logs_dir=args.cluster_logs_dir), shell=True)

    ## save to configs.yaml in wdir
    cf.write_configfile(os.path.join(args.wdir,'config.yaml'),config)

    ## cluster config
    cluster_config = cf.load_configfile(os.path.join(this_script_dir,"../../shared/","cluster.yaml"),False)
    cluster_config = cf.merge_dicts(cf.load_configfile(os.path.join(this_script_dir,"cluster.yaml"),False), cluster_config)
    
    if args.cluster_configfile:
        user_cluster_config = cf.load_configfile(args.cluster_configfile,False)
        cluster_config = cf.merge_dicts(cluster_config, user_cluster_config) # 2) form user_config.yaml
    cf.write_configfile(os.path.join(args.wdir,'cluster_config.yaml'),cluster_config)
 
    if not args.local:
        snakemake_module_load = "module load snakemake/3.12.0 " #3.12 #4.2.0 #3.7.1
        snakemake_module_load += cluster_config["cluster_module_load"]
     
        snakemake_module_load = (snakemake_module_load + " && ").split()

    snakemake_cmd = """
                    snakemake {snakemake_options} --latency-wait 300 --snakefile {snakefile} --jobs {max_jobs} --directory {wdir} --configfile {configfile}
                    """.format( snakefile = os.path.join(args.this_script_dir, "Snakefile"),
                                max_jobs = args.max_jobs,
                                wdir = args.wdir,
                                snakemake_options = str(args.snakemake_options or ''),
                                configfile = os.path.join(args.wdir,'config.yaml')
                              ).split()
    if args.verbose:
        snakemake_cmd.append("--printshellcmds")

    if not args.local:
        snakemake_cmd += ["--cluster-config ",
        os.path.join(args.wdir,'cluster_config.yaml'),
        " --cluster \'", cluster_config["snakemake_cluster_cmd"],
        args.cluster_logs_dir, "--name {rule}.snakemake'"]

    print(snakemake_cmd)

    snakemake_log = "2>&1 | tee -a {}/WGBSpipeline.log".format(args.wdir).split()

    ## create local temp dir and add this path to environment as $TMPDIR variable
    ## on SLURM: $TMPDIR is set, created and removed by SlurmEasy on cluster node
    temp_path = cf.make_temp_dir(args.tempdir, args.wdir, args.verbose)
    snakemake_exports = ("export TMPDIR="+temp_path+" && ").split()

    cmd = " ".join(snakemake_exports + snakemake_module_load + snakemake_cmd + snakemake_log)

    if args.verbose:
        print("\n", cmd, "\n")

    ## Write snakemake_cmd to log file
    with open(os.path.join(args.wdir,"WGBSpipeline.log"),"w") as f:
        f.write(" ".join(sys.argv)+"\n\n")
        f.write(cmd+"\n\n")

    ## Run snakemake
    p = subprocess.Popen(cmd, shell=True)
    if args.verbose:
        print("PID:", p.pid, "\n")
    try:
        p.wait()
    except:
        print("\nWARNING: Snakemake terminated!!!")
        if p.returncode != 0:
            if p.returncode:
                print("Returncode:", p.returncode)

            # kill snakemake and child processes
            subprocess.call(["pkill", "-SIGTERM", "-P", str(p.pid)])
            print("SIGTERM sent to PID:", p.pid)

    ## remove temp dir
    if (temp_path != "" and os.path.exists(temp_path)):
        shutil.rmtree(temp_path, ignore_errors=True)
        if args.verbose:
            print("temp dir removed: "+temp_path+"\n")


if __name__ == "__main__":
    main()
