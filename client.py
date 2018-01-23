'''The client.'''

import argparse
import datetime
import json
import os
import sys
import time

from collections import Sequence

from lib.utils import print_msg, FLock
from lib.runner import BaseRunner


DAEMON_IN = '/home/chayan/stuffs/hat/ipc/daemon_in.fifo'
DAEMON_OUT = '/home/chayan/stuffs/hat/ipc/daemon_out.fifo'


class HatClientException(Exception):
    '''Generic exception class for the client.'''
    pass
        
def parse_arguments():
    '''Parse arguments (for client) and
    return appropriate response back.
    '''
    # if not args:
    #     print_msg('Not enough options/arguments given')
    #     return
    parser = argparse.ArgumentParser(description='hat client')
    parser.add_argument('-l', '--list', dest='joblist',
                        required=False, action='store_true',
                        help='Show the list of queued jobs for current user')
    parser.add_argument('-c', '--count', dest='jobcount',
                        required=False, action='store_true',
                        help='Show the number of queued jobs for current user')
    parser.add_argument('-a', '--add', dest='add_job',
                        metavar='JOB SPEC', nargs='+',
                        required=False, help='Add a new job')
    parser.add_argument('-r', '--remove', dest='remove_job',
                        metavar='JOB ID', nargs='+',
                        required=False, help='Add a new job')
    
    args_ns = parser.parse_args()
    args_dict = vars(args_ns)
    return args_dict


def argument_serializer(args_dict):
    '''Checks the argument dict, and returns the args
    as a sequence after passing them through decision logic.
    '''    
    if not any(args_dict.values()) or args_dict.get('joblist'):
        return ('joblist',)
    elif args_dict.get('jobcount'):
        return ('jobcount',)
    elif args_dict.get('add_job'):
        return ('add_job', *args_dict.get('add_job'))
    elif args_dict.get('remove_job'):
        return ('remove_job', *args_dict.get('remove_job'))
    return


class ProcessSend:
    '''Takes and parses input, based on key creates and
    sends appropriate JSON for daemon. Input content must
    be a sequence with first element being the desired key.
    '''
    def __init__(self, content):
        if not isinstance(content, Sequence):
            raise HatClientException('Input must be a sequence')
        self.content = content
        self.key_format_map = {
            'add_job': self.add_job_fmt,
            'remove_job': self.remove_job_fmt,
            'joblist': self.joblist_fmt,
            'jobcount': self.jobcount_fmt,
        }

    def check_get_send(self):
        '''Sending sliced data to specific formatters, after
        looking up the fmt func using key (first element).
        If all goes good, sending to daemon fifo.
        '''
        try:
            self.key_format_map[self.content[0]](self.content[1:])
        except KeyError:
            raise HatClientException('Ambiguous input')
        self.send_to_daemon()
        
    def add_job_fmt(self, data):
        if len(data) not in {2, 3}:
            raise HatClientException('Ambiguous input')
        command = '{} -c "{}"'.format(data[2], data[0]) if data[2] else data[0]
        self.out_dict = {
            'add_job': {
                'euid': os.geteuid(),
                'command': command,
                'time_': data[1],
                'use_shell': data[2] if len(data) == 3 else False
            }
        }

    def remove_job_fmt(self, data):
        try:
            data = [int(i) for i in data]
        except ValueError:
            raise HatClientException('Ambiguous input')
        self.out_dict = {
            'remove_job': (os.geteuid(), *data)
        }

    def joblist_fmt(self, _):
        self.out_dict = {
            'joblist': os.geteuid()
        }

    def jobcount_fmt(self, _):
        self.out_dict = {
            'jobcount': os.geteuid()
        }

    def send_to_daemon(self):
        BaseRunner.write_to_file(
            DAEMON_IN,
            json.dumps(self.out_dict),
            'wt',
            True
        )

        
if __name__ == '__main__':
    if len(sys.argv) == 1:
        print_msg('Not enough options/arguments')
        exit(127)
    args_dict = parse_arguments()
    data_seq = argument_serializer(args_dict)
    if not data_seq:
        print_msg('Ambiguous input')
        exit(126)
    data = ProcessSend(data_seq)
    data.check_get_send()
    time.sleep(1)
    with open(DAEMON_OUT) as f:
        while True:
            for line in f:
                print(json.loads(line))

    
