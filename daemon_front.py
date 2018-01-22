'''Front facing interface of the daemon, for abstracting the daemon.'''

import json
import sys
import time

from collections import Mapping

from lib.runner import BaseRunner
from daemon import HatDaemon


DAEMON_IN = '/home/chayan/stuffs/hat/ipc/daemon_in.fifo'
DAEMON_OUT = '/home/chayan/stuffs/hat/ipc/daemon_out.fifo'


class DaemonWrapper:
    def __init__(self, daemon):
        self.daemon = daemon
        # dict values are wrappers that calls the
        # underlying relevant daemon function
        self.input_to_operation_map = {
            'add_job': self.add_job,
            'remove_job': self.remove_job,
            'joblist': self.joblist,
            'jobcount': self.jobcount,
        }
        
    def add_job(self, value):
        '''Adds a new job.'''
        return self.daemon.add_job(**dict(value))

    def remove_job(self, value):
        '''Removes a job.'''
        return self.daemon.remove_job(*value)

    def _write_daemon_out(self, output):
        '''Writes the output to the daemon_out fifo.'''
        BaseRunner.write_to_file(
            DAEMON_OUT,
            json.dumps(output),
            mode='wt',
            nodate=True,
        )
    
    def joblist(self, value):
        '''Returns the joblist of UID - value.'''
        output = self.daemon.joblist(int(value))
        self._write_daemon_out(output)
        
    def jobcount(self, value):
        '''Returns the jobcount of UID - value.'''
        output = self.daemon.jobcount(int(value))
        self._write_daemon_out(output)

    def parse_check_forward(self, content):
        '''Takes the input content, checks validity;
        if valid, passes to upstream, discards otherwise.
        '''
        if not isinstance(content, Mapping):
            return
        operation, value = next(iter(content.items()))
        try:
            self.input_to_operation_map[operation](value)
        except KeyError:
            return
        
    def run(self):
        '''Runs continuously, gets input from fifo, sends
        those for processing to parse_check_forward.
        '''
        with open(DAEMON_IN, 'rt') as d_in:
            while True:
                for line in d_in:
                    try:
                        content = json.loads(line)
                    except json.JSONDecodeError:
                        pass
                    else:
                        self.parse_check_forward(content)
                time.sleep(0.1)

    
if __name__ == '__main__':
    daemon = HatDaemon()
    # Start-stop
    if len(sys.argv) == 2:
        action_map = {
            'start': daemon.start,
            'stop': daemon.stop
        }
        if sys.argv[1] in action_map:
            action_map[sys.argv[1]]()
    # if daemon is started, starting to `run`
    if daemon.status():
        daemon_wrapper = DaemonWrapper(daemon)
        daemon_wrapper.run()

