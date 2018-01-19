'''The base job runner and associative stuffs.'''

import datetime
import multiprocessing
import os
import shlex
import subprocess
import time

from .scheduler import get_enqueued_jobs, remove_job


class HatRunnerException(Exception):
    '''Generic exception class for base runner.'''
    pass


class BaseRunnerMeta(type):
    '''Metaclass to make sure that BaseRunner is a singleton.'''
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]
    

class BaseRunner(metaclass=BaseRunnerMeta):
    '''The base command runner. This is a singleton.'''
    def __init__(self):
        self.stdout = '/home/chayan/stuffs/hat/logs/hat/stdout.log'
        self.stderr = '/home/chayan/stuffs/hat/logs/hat/stderr.log'

    @property
    def jobcount(self):
        '''Returns number of runnable jobs in the queue.'''
        return len(get_enqueued_jobs())

    @property
    def joblist(self):
        return list(get_enqueued_jobs().values())

    @property
    def _joblist_raw(self):
        return get_enqueued_jobs()
    
    def start(self):
        '''Starting BaseRunner instance.'''
        self._running = True
        self.pool = multiprocessing.Pool()
        self._runner()

    def stop(self):
        '''Stopping BaseRunner instance.'''
        self._running = False

    def _runner(self):
        '''The runner.'''
        while True:
            if not self._running:
                break
            _jobs = self._joblist_raw
            if _jobs:
                to_remove = []
                for hash_, job in _jobs.items():
                    if job['job_run_at'] <= int(time.time()):
                        self.pool.apply_async(
                            self.run_command,
                            args=(job['command'],),
                            kwds={
                                'stdout': self.stdout,
                                'stderr': self.stderr,
                            }
                        )
                        to_remove.append(hash_)
                for hash_ in to_remove:
                    remove_job(hash_)
            time.sleep(0.1)
            
    @staticmethod    
    def run_command(command, stdout, stderr):
        for f in (stdout, stderr):
            if f:
                os.makedirs(os.path.dirname(f), exist_ok=True)
                
        with open(stdout, 'at') as f_out, open(stderr, 'at') as f_err:
            try:
                process = subprocess.Popen(shlex.split(command),
                                           stdout=f_out,
                                           stderr=f_err,
                                           shell=False)
            except FileNotFoundError as err:
                f_err.write(str(err))
            else:
                return process

