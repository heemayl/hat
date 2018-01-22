'''The daemon and related stuffs of hat.'''

import json
import multiprocessing
import subprocess
import time

from lib.runner import BaseRunner


class HatDaemonMeta(type):
    '''Metaclass to ensure HatDaemon singleton.'''
    _instances = {}
    
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class HatDaemon(metaclass=HatDaemonMeta):
    def __init__(self):
        self.runner = BaseRunner()
        self.daemon = multiprocessing.Process(
            target=self.runner.start,
            # daemon=True,
            name='hatd',
        )
        self.runner_in = '/home/chayan/stuffs/hat/ipc/daemon_in.fifo'
        self.runner_out = '/home/chayan/stuffs/hat/ipc/daemon_out.fifo'
        
    def start(self):
        '''Starting the daemon.'''
        self.daemon.start()
        time.sleep(1)
        if self.status():
            return True
        return False

    def stop(self):
        '''Stop should be foreceful, if needed.'''
        self.runner.stop()
        if not self.status():
            self.daemon.terminate()
        if not self.status():
            subprocess.call(
                'kill -9 {}'.format(self.daemon.pid),
                shell=True
            )
        return True
            
    def status(self):
        return self.daemon.is_alive()

    @property
    def status_verbose(self):
        if self.status():
            return 'Running'
        return 'Not running'
    
    @property
    def pid(self):
        return self.daemon.pid

    def add_job(self, command, time_, use_shell=False):
        '''Adds a new job.'''
        # Sending `job` dict to fifo with required params
        job = {
            'command': command,
            'time_': time_,
            'use_shell': use_shell
        }
        BaseRunner.write_to_file(self.runner_in, json.dumps(job), 'wt',
                                 nodate=True)
        
    def remove_job(self, job_id):
        '''Remove a job.'''
        # Sending a dict with `remove` as key
        # and job_id as value
        remove_job = {
            'remove': job_id
        }
        BaseRunner.write_to_file(self.runner_in, json.dumps(remove_job),
                                 'wt', nodate=True)
        
    @property
    def joblist(self):
        '''Getting the current joblist as raw dict.'''
        # Sending one item dict with key `joblist`
        content = {
            'joblist': True
        }
        BaseRunner.write_to_file(self.runner_in, json.dumps(content), 'wt',
                                 nodate=True)
        with open(self.runner_out) as runner_out:
            jobs = runner_out.read().strip()
        jobs = json.loads(jobs)
        return jobs

    @property
    def jobcount(self):
        jobs = self.joblist
        return len(jobs)
    
    
if __name__ == '__main__':
    pass
