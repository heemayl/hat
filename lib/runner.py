'''The base job runner and associative stuffs.'''

import datetime
import multiprocessing
import os
import shlex
import subprocess
import time

from collections import Mapping, Sequence

from .scheduler import Job, get_enqueued_jobs, remove_job
from .utils import FLock


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
        self.stdout_file = '/home/chayan/stuffs/hat/logs/hat/stdout.log'
        self.stderr_file = '/home/chayan/stuffs/hat/logs/hat/stderr.log'
        self._running = False
        self.queue = multiprocessing.Queue()
        
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

    def get_queue(self):
        return self.queue
        
    def start(self):
        '''Starting BaseRunner instance.'''
        self._running = True
        self._runner(self.queue)

    def stop(self):
        '''Stopping BaseRunner instance.'''
        # Sending a sequence to the queue with
        # first element being the string `stop`
        self.queue.put_nowait(('stop',))

    def _runner(self, queue):
        '''The runner.'''
        while True:
            try:
                item = queue.get_nowait()
            except Exception:
                pass
            else:
                # Jobs come as dicts
                if isinstance(item, Mapping):
                    try:
                        Job(item['command'], item['time_'])
                    except KeyError:
                        pass
                elif isinstance(item, Sequence):
                    # Stop runner if the first element of sequence is `stop`
                    if item[0] == 'stop':
                        self._running = False
            if not self._running:
                break
            _jobs = self._joblist_raw
            if _jobs:
                to_remove = []
                for hash_, job in _jobs.items():
                    if job['job_run_at'] <= int(time.time()):
                        multiprocessing.Process(
                            target=self.command_run_save,
                            args=(job['command'],),
                            kwargs={
                                'stdout_file': self.stdout_file,
                                'stderr_file': self.stderr_file,
                                'use_shell': job.get('use_shell', False)
                            },
                        ).start()
                        to_remove.append(hash_)
                for hash_ in to_remove:
                    remove_job(hash_)
            time.sleep(0.1)

    def command_run_save(self, command, stdout_file, stderr_file,
                         use_shell=False):
        '''Runs a command using `run_command`, gets the
        (returncode, STDOUT, STDERR) tuple and saves them
        using `_check_and_write`.
        '''
        for f in (stdout_file, stderr_file):
            if f:
                os.makedirs(os.path.dirname(f), exist_ok=True)

        returncode, stdout, stderr = self.run_command(command, use_shell)
        self._check_and_write(stdout_file, command, returncode, stdout)
        self._check_and_write(stderr_file, command, returncode, stderr)

    def run_command(self, command, use_shell):
        '''Runs a command, and returns (exit_status, STDOUT, STDERR) tuple.'''
        try:
            command_ = command if use_shell else shlex.split(command)
            proc = subprocess.Popen(command_,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    shell=use_shell)
        except Exception as err:
            # Setting `returncode` to 127
            returncode, stdout, stderr = 127, b'', bytes(str(err), 'utf-8')
        else:
            returncode, stdout, stderr = proc.wait(), *proc.communicate()
        finally:
            return (returncode, stdout, stderr)

    def _check_and_write(self, filename, command, returncode, content):
        '''Checks the input content, converts and saves in
        filename by calling `write_to_file` afterwards.
        '''
        if content:
            content = '{} : {} :: {}'.format(command, returncode,
                                             content.decode('utf-8'))
            self.write_to_file(filename, content)
            
    @staticmethod
    def write_to_file(filename, content, mode='at'):
        '''Writes `content` to `filename`.'''
        with FLock():
            with open(filename, mode) as f:
                f.write('{} : {}\n'.format(
                    datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    content)
                )

                
if __name__ == '__main__':
    pass

