'''Parser of hat logs. Comes with `hatd`.'''

import argparse
import datetime
import glob
import gzip
import os
import re
import sys

from lib.utils import print_msg


# Constants
USER_LOG_LOCATION = os.path.expanduser('~/.hatd/logs/')


def split_format(line):
    '''Takes a line as input and returns
    splitted-formatted fields as output.
    '''
    dt_format = '%Y-%m-%d %H:%M:%S'
    splitted_line = line.split(' :')

    run_time = splitted_line[0].strip()
    run_time_dt = datetime.datetime.strptime(run_time, dt_format)
    
    euid = splitted_line[1].split('>')[1].strip()
    job_id = splitted_line[2].split('>')[1].strip()
    
    scheduled_time = splitted_line[3].split('>')[1].strip()
    scheduled_time_dt = datetime.datetime.strptime(scheduled_time, dt_format)
    
    command = splitted_line[4].split('>')[1].strip()
    return_code = splitted_line[5].split('>')[1].strip()
    output = splitted_line[-1].split('>', maxsplit=1)[1].strip()

    return (run_time_dt, euid, job_id, scheduled_time_dt,
            command, return_code, output)


def parse_arguments():
    '''Parse arguments (for logs) and
    return appropriate response back.
    '''
    parser = argparse.ArgumentParser(prog='hat-parser',
                                     description='Log parser for hatc – a client for HAT (Hyper-AT), the one-time scheduler for GNU/Linux. Without any option, it shows all STDOUT logs.')
    parser.add_argument('-c', '--command', dest='command',
                        required=False, help='Part of the command used (Regex supported).\n')
    parser.add_argument('-e', '--error', dest='stderr', action='store_true',
                        required=False, help='Show error messages.')
    parser.add_argument('-s', '--scheduled', dest='scheduled', action='store_true',
                        required=False, help='Compare against scheduled time of jobs instead of run time (default).')
    parser.add_argument('-f', '--from', dest='from_time',
                        required=False, help='Show logs starting from this time (including). Must be in format YYYY-mm-ddTHH:MM:SS (e.g. 2018-02-04T14:34:00, 2017-12-23T02:23:45).\n')
    parser.add_argument('-t', '--to', dest='to_time',
                        required=False, help='Show logs upto this time (including). Must be in format YYYY-mm-ddTHH:MM:SS (e.g. 2018-04-14T23:31:04, 2017-12-31T09:12:45).\n')
    
    args_ns = parser.parse_args()
    args_dict = vars(args_ns)
    return args_dict


def search_params_formatter(args_dict):
    '''Takes the argument dict as input and returns
    the appropriate search parameters as a tuple.
    Sets appropriate defaults if needed.
    '''
    command_re = args_dict.get('command') or '.'
    logtype = args_dict.get('stderr') or 'stdout'
    compare_sched = args_dict.get('scheduled', False)
    # I think it's safe to take the start of 2018
    # as the starting time if nothing given
    start_time = args_dict.get('from_time') or '2018-01-01T00:00:00'
    # We'll take end of today as the end time if nothing given
    end_time = args_dict.get('to_time') or datetime.datetime.strftime(
        datetime.datetime.now(),
        '%Y-%m-%dT23:59:59')
    try:
        start_dt = datetime.datetime.strptime(start_time,
                                              '%Y-%m-%dT%H:%M:%S'
        )
        end_dt = datetime.datetime.strptime(end_time,
                                            '%Y-%m-%dT%H:%M:%S'
        )
    except ValueError:
        print_msg(
            'Datetime must be in format `YYYY-mm-ddTHH:MM:SS`. See `hat-parser --help`.',
            file=sys.stderr
        )
        exit(1)
    return (command_re, logtype, compare_sched, start_dt, end_dt)


def main():
    '''Main function that calls others to get data and
    then iterates over the files line by line.'''
    command_re, logtype, compare_sched, start_dt, end_dt = (
        search_params_formatter(parse_arguments()))
    logfile_glob = os.path.join(USER_LOG_LOCATION, '{}.log*'.format(logtype))
    logfiles = glob.iglob(logfile_glob)
    # Log lines start with appropriately formatted datetime 
    dt_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}\s+(?:\d{2}:){2}\d{2}')
    for file_ in logfiles:
        # Setting appropriate open function
        # expecting .gz extension or as-is
        open_ = gzip.open if file_.endswith('.gz') else open
        with open_(file_, mode='rt') as f:
            # This keeps track if the line containing
            # dt has been printed already; need this
            # to handle multiline logs
            dt_line_printed = False
            for line in f:
                line = line.rstrip()
                if not line:
                    continue
                # If the line does not start with datetime, it is a
                # multiline log so printing it and continuing the
                # loop without the datetime comparison
                if (not dt_pattern.search(line)):
                    if dt_line_printed:
                        print_msg(line, end='')  # log lines already contain blank lines
                    continue
                (run_time_dt, euid, job_id, scheduled_time_dt,
                 command, return_code, output) = split_format(line)
                # Comparing dt field
                compare_dt = scheduled_time_dt if compare_sched else run_time_dt
                if start_dt <= compare_dt <= end_dt:
                    print_msg(line, end='')
                    dt_line_printed = True
                # Break out of this file if we're already passed
                # the end dt and we're comparing run time
                else:
                    dt_line_printed = False
                    if not compare_sched and compare_dt > end_dt:
                        break
                
    
if __name__ == '__main__':
    main()

