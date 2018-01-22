'''Generic scheduling stuffs for all incoming jobs. Other
modules only need to work with `enqueued_jobs` dict.
'''

import collections
import datetime
import os
import pickle
import time

from abc import ABCMeta

from .utils import FLock


pickle_file = '/home/chayan/stuffs/hat/hatdb.pkl'
daemon_log = '/home/chayan/stuffs/hat/logs/hat/daemon.log'

# Loading previous jobs (if any)
with open(pickle_file, 'rb') as fpkl:
    try:
        saved_data = pickle.load(fpkl)
    except EOFError:
        saved_data = None
        
enqueued_jobs = saved_data or collections.defaultdict(dict)


def _check_perm(euid):
    '''Check if the given EUID is allowed.'''
    invoking_euid = os.geteuid()
    # TODO: Need to change this because `os.getuid()` will
    # always be 0 as root would start the daemon
    if invoking_euid not in {euid, 0}:
        invoking_euid = os.geteuid()
        write_daemon_log("UID {} can't impersonate UID {}"
                         .format(invoking_euid, euid))
        raise HatJobException(
            'UID {}: Permission denied while impersonating UID {}'.format(
                invoking_euid, euid))
    

def write_daemon_log(content):
    '''DRY func for writing to the daemon log.'''
    with FLock():
        with open(daemon_log, 'at') as f:
            f.write('{} : {}\n'.format(
                datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                content
            ))
    

def get_enqueued_jobs(euid):
    '''To be called from other modules to get enqueued_jobs.'''
    # if euid is -1, dumps everything
    # TODO: Anything more creative (and robust)?
    if euid == -1:
        return enqueued_jobs
    _check_perm(euid)
    return enqueued_jobs.get(euid, {})


def remove_job(euid, job_id):
    '''Remove a job from enqueued_jobs based on job ID.'''
    _check_perm(euid)
    jobs = get_enqueued_jobs(euid)
    try:
        del jobs[job_id]
    except KeyError:
        with open(daemon_log, 'a') as f:
            f.write('{} : {}\n'.format(
                datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'Removal failed: No such job with ID {} for UID {}'.
                format(job_id, euid)
            ))

        
class HatTimerException(Exception):
    '''Generic exception class for all input timers.'''
    pass


class HatJobException(Exception):
    '''Generic exception for jobs.'''
    pass


class JobMeta(ABCMeta):
    '''Setting the allowed `strptime` formats for
    all classed.
    '''
    def __new__(mtcls, cls_name, bases, attrs):
        try:
            _ = attrs['allowed_strptimes']
        except KeyError:
            allowed_strptimes = [
                '%Y-%m-%d_%H:%M:%S',
                '%Y-%m-%d %H:%M:%S',
            ]
            attrs['allowed_strptimes'] = allowed_strptimes
        return super().__new__(mtcls, cls_name, bases, attrs)
                

class Job(metaclass=JobMeta):
    '''A job to be done at specified time.'''
    def __init__(self, euid, command, time_, use_shell=False):
        self.euid = euid
        self.command = command
        self.time_str = time_
        self.use_shell = use_shell
        # Checking Permission
        _check_perm(self.euid)
        # Getting when to run in Epoch 
        self.date_time_epoch = self.get_run_at_epoch()
        # Saving the job, with the user's EUID as keys, and increasing
        # IDs as subdict keys with command, time, use_shell as values
        self.job_id = self._get_job_id()
        enqueued_jobs[int(euid)].update({
            self.job_id: {
                'command': self.command,
                'job_run_at': int(self.date_time_epoch),  # to int
                'use_shell': self.use_shell,
            }
        })

    def _get_job_id(self):
        '''Get job ID, to be used as the Job dict key.'''
        # We'll wrap around at 40000
        max_id = 40000
        current_keys = set(i for v in enqueued_jobs.values()
                           for i in v.keys())
        current_id = max(current_keys) if current_keys else 0
        next_id = current_id + 1
        if next_id <= max_id and next_id not in current_keys:
            return next_id
        for id in range(1, max_id):
            if id not in current_keys:
                return id
        raise HatJobException(
            'Job slot exceeded: Maximum {} jobs can be enqueued'
            .format(max_id))
        
    def get_run_at_epoch(self):
        '''Returns when to run the job in Epoch, raises
        expection for any invalid/incorrect input time.
        '''
        self.date_time = None
        for strptime in self.allowed_strptimes:
            try:
                self.date_time = datetime.datetime.strptime(
                    self.time_str, strptime)
            except ValueError:
                continue
            else:
                return time.mktime(self.date_time.timetuple())
        if not self.date_time:
            raise HatTimerException(('Ambiguous input time: {}'
                                     '. Please see the help page.')
                                    .format(self.time_str))
        if self.date_time_epoch <= time.time():
            raise HatTimerException('No backward time travel support: {}'
                                    .format(self.time_str))

    def __repr__(self):
        return 'Hat Job: <{}>at<{}>'.format(self.command,
                                            self.time_str)

    
if __name__ == '__main__':
    pass

