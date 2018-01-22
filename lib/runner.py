'''The base job runner and associative stuffs.'''

import datetime
import json
import multiprocessing
import os
import shlex
import subprocess
import time

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
        self.daemon_log = '/home/chayan/stuffs/hat/logs/hat/daemon.log'
        self.fifo_in = '/home/chayan/stuffs/hat/ipc/daemon_in.fifo'
        self.fifo_out = '/home/chayan/stuffs/hat/ipc/daemon_out.fifo'
        self._running = False
        self.queue = multiprocessing.Queue()
        
    @property
    def _joblist_raw(self):
        return get_enqueued_jobs()

    def start(self):
        '''Starting BaseRunner instance.'''
        self._running = True
        self._runner(self.fifo_in, self.fifo_out)

    def stop(self):
        '''Stopping BaseRunner instance.'''
        # Sending an one item dict with key `stop`
        content = json.dumps({'stop': True})
        self.write_to_file(self.fifo_in, content, 'wt', nodate=True)

    def _runner(self, fifo_in, fifo_out):
        '''The runner.'''
        with open(fifo_in, 'rt') as fifo_in:
            while True:
                to_remove = []
                for line in fifo_in:
                    try:
                        content = json.loads(line.strip())
                    except json.JSONDecodeError as e:
                        self.write_to_file(self.daemon_log, str(e))
                    else:
                        if len(content) == 3:
                            try:
                                Job(
                                    content['command'],
                                    content['time_'],
                                    content.get('use_shell', False)
                                )
                            except KeyError:
                                pass
                        elif len(content) == 1:
                            if 'joblist' in content:
                                self.write_to_file(fifo_out,
                                                   json.dumps(
                                                       dict(self._joblist_raw)
                                                   ),
                                                   mode='wt',
                                                   nodate=True
                                )
                            elif 'stop' in content:
                                self._running = False
                            elif 'remove' in content:
                                to_remove.append(int(content['remove']))
                if not self._running:
                    break
                _jobs = self._joblist_raw
                if _jobs:
                    for job_id, job in _jobs.items():
                        if job['job_run_at'] <= int(time.time()):
                            multiprocessing.Process(
                                target=self.command_run_save,
                                args=(job['command'],),
                                kwargs={
                                    'stdout_file': self.stdout_file,
                                    'stderr_file': self.stderr_file,
                                    'use_shell': job.get('use_shell', False),
                                    'job_id': job_id
                                },
                            ).start()
                            to_remove.append(job_id)
                    for job_id in to_remove:
                        remove_job(job_id)
                time.sleep(0.1)

    def command_run_save(self, command, stdout_file, stderr_file,
                         use_shell, job_id):
        '''Runs a command using `run_command`, gets the
        (returncode, STDOUT, STDERR) tuple and saves them
        using `_check_and_write`.
        '''
        for f in (stdout_file, stderr_file):
            if f:
                os.makedirs(os.path.dirname(f), exist_ok=True)

        returncode, stdout, stderr = self.run_command(command, use_shell,
                                                      job_id)
        self._check_and_write(stdout_file, job_id, command, returncode, stdout)
        self._check_and_write(stderr_file, job_id, command, returncode, stderr)

    def run_command(self, command, use_shell, job_id):
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
            try:
                return (returncode, stdout, stderr)
            except UnboundLocalError:
                # Interactive or frame refreshing commands
                # are not allowed e.g. `top`
                error_msg = ('Interactive or screen refreshing'
                             ' commands are not allowed'
                )
                self.write_to_file(
                    self.daemon_log,
                    'id>{} : cmd>{} :: {}'.format(job_id, command, error_msg)
                )
                # raise HatRunnerException(error_msg)
            
    def _check_and_write(self, filename, job_id, command, returncode, content):
        '''Checks the input content, converts and saves in
        filename by calling `write_to_file` afterwards.
        '''
        if content:
            content = 'id>{} : cmd>{} : ret>{} :: out>{}'.format(
                job_id, command, returncode, content.decode('utf-8'))
            self.write_to_file(filename, content)
            
    @staticmethod
    def write_to_file(filename, content, mode='at', nodate=False):
        '''Writes `content` to `filename`.'''
        with FLock():
            with open(filename, mode) as f:
                f.write('{} : {}\n'.format(
                    datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    content,
                )
                ) if not nodate else f.write('{}\n'.format(
                    content)
                )
                

if __name__ == '__main__':
    pass
