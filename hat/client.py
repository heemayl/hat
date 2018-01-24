'''The client.'''

import argparse
import datetime
import json
import os
import shlex
import subprocess
import sys
import time

from collections import Sequence

from lib.utils import print_msg, read_file, write_file


DAEMON_IN = '/home/chayan/stuffs/hat/ipc/daemon_in.fifo'
DAEMON_OUT = '/home/chayan/stuffs/hat/ipc/daemon_out.fifo'
DAEMON_PID_FILE = '/home/chayan/stuffs/hat/hatd.pid'


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
                        metavar='<command> <datetime> [<shell>]', nargs='+',
                        required=False, help='Add a new job')
    parser.add_argument('-r', '--remove', dest='remove_job',
                        metavar='<JOB_ID>', nargs='+',
                        required=False, help='Remove queued job(s)')
    
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


def check_daemon_process(pid_file):
    '''Checks if the daemon process exists.'''
    if not os.path.isfile(pid_file):
        return False
    pid = read_file(
        pid_file,
        whole=True
    )
    proc = subprocess.Popen(
        shlex.split('/bin/ps -p {} -o cmd='.format(pid)),
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        )
    ret = proc.wait()
    if not ret or b'hat/daemon_front.py' in proc.communicate()[0]:
        return True
    return False
    
    
class SendReceiveData:
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
            'stop_daemon': self.stop_daemon,
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
        command = '{} -c "{}"'.format(data[2], data[0]) if len(data) == 3 \
                  else data[0]
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

    def stop_daemon(self, _):
        self.out_dict = {
            'stop': True
        }

    def send_to_daemon(self):
        write_file(
            DAEMON_IN,
            self.out_dict,
            mode='wt',
            nodate=True,
            json_dumps=True
        )

    def receive_from_daemon(self):
        return read_file(
            DAEMON_OUT,
            whole=True,
            json_loads=True
        )

    
def main():
    if len(sys.argv) == 2:
        if sys.argv[1] == 'stop_daemon':
            if os.geteuid():
                print_msg('Unknown operation')
                exit(1)
            data_seq = ('stop_daemon', True)
            data = SendReceiveData(data_seq)
            data.check_get_send()
            exit(0)
    if not check_daemon_process(DAEMON_PID_FILE):
        print_msg('Daemon (hatd) is not running')
        exit(127)
    args_dict = parse_arguments()
    data_seq = argument_serializer(args_dict)
    if not data_seq:
        print_msg('Ambiguous input')
        exit(126)
    data = SendReceiveData(data_seq)
    data.check_get_send()
    received = data.receive_from_daemon()
    if received is not None:
        print(received)

        
if __name__ == '__main__':
    main()
    
