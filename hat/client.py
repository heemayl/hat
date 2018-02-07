'''The client.'''

import argparse
import os
import shlex
import subprocess
import sys
import time

from collections import Sequence

from lib.utils import print_msg, read_file, write_file, username_from_euid
from lib.humantime_epoch_converter import main as get_epoch_main


DAEMON_IN = '/var/run/hatd/ipc/daemon_in.fifo'
DAEMON_OUT = '/var/run/hatd/ipc/daemon_out.fifo'
DAEMON_PID_FILE = '/var/run/hatd/hatd.pid'
USER_DIR = '/home/{}/.hatd'.format(username_from_euid(os.geteuid())) \
           if os.geteuid != 0 else '/root/.hatd'


class HatClientException(Exception):
    '''Generic exception class for the client.'''
    pass


def create_user_files():
    '''Create necessary dirs and files
    for the invoking user.
    '''
    os.makedirs('{}/logs'.format(USER_DIR), mode=0o700, exist_ok=True)
    for file_ in {'stdout.log', 'stderr.log'}:
        file_ = '{}/logs/{}'.format(USER_DIR, file_)
        if not os.path.isfile(file_):
            with open(file_, 'wt') as f:
                f.write('')

                
def parse_arguments():
    '''Parse arguments (for client) and
    return appropriate response back.
    '''
    parser = argparse.ArgumentParser(prog='hatc', description='hat client',
                                     formatter_class=argparse.
                                     RawTextHelpFormatter)
    parser.add_argument('-l', '--list', dest='joblist',
                        required=False, action='store_true',
                        help='Show the list of queued jobs for current user\n')
    parser.add_argument('-c', '--count', dest='jobcount',
                        required=False, action='store_true',
                        help='Show the number of queued jobs for current user\n')
    parser.add_argument('-a', '--add', dest='add_job',
                        metavar='<command> <datetime_spec> [<shell>]', nargs='+',
                        required=False, help="""Add a new job. If shell is specified, the job will be run in the given shell, otherwise no shell will be used. Example:

        hatc --add 'free -m' 'now + 30 min'
        hatc -a 'tail -10 /var/log/syslog' 'tomorrow at 14:30'
        hatc -a 'func() { echo Test ;}; func()' 'next sunday 11' bash
        hatc -a 'echo $PATH' 'today 18:06:34' dash
        hatc -a date 'tomorrow 10 - 6 hr 12 min 3 sec'

        More on <datetime_spec>: https://github.com/heemayl/humantime-epoch-converter
        Job's STDOUT, STDERR will be logged in `~/.hatd/logs/{stdout,stderr}.log`, respectively.
        """
    )
    parser.add_argument('-r', '--remove', dest='remove_job',
                        metavar='<JOB_ID>', nargs='+',
                        required=False, help="""Remove queued job(s) by Job ID. Example:

        hatc --remove 12
        hatc -r 3 8 23
        """
    )
    
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
        time_ = time.strftime('%Y-%m-%d_%H:%M:%S',
                              time.localtime(get_epoch_main(data[1])))
        
        self.out_dict = {
            'add_job': {
                'euid': os.geteuid(),
                'command': command,
                'time_': time_,
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
    create_user_files()
    data = SendReceiveData(data_seq)
    data.check_get_send()
    received = data.receive_from_daemon()
    if received is not None:
        print(received)

        
if __name__ == '__main__':
    main()
    
