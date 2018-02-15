'''Generic scheduling stuffs for all incoming jobs. Other
modules only need to work with `enqueued_jobs` dict.
'''

import collections
import datetime
import os
import pickle
import re
import time

from abc import ABCMeta

from .utils import write_file


PICKLE_FILE = '/var/lib/hatd/hatdb.pkl'
DAEMON_LOG = '/var/log/hatd/daemon.log'

# Loading previous jobs (if any)
try:
    with open(PICKLE_FILE, 'rb') as fpkl:
        try:
            saved_data = pickle.load(fpkl)
        except EOFError:
            saved_data = None
except FileNotFoundError:
    saved_data = None
        
enqueued_jobs = saved_data or collections.defaultdict(dict)


def _check_perm(euid):
    '''Check if the given EUID is allowed.'''
    daemon_euid = os.geteuid()
    # TODO: Need to change this because `os.getuid()` will
    # always be 0 as root would start the daemon
    if euid not in {daemon_euid, 0}:
        write_file(
            DAEMON_LOG,
            "UID {}: Permission denied".format(euid),
            mode='at',
        )
        
        raise HatJobException(
            'UID {}: Permission denied'.format(euid))


def get_enqueued_jobs(euid):
    '''To be called from other modules to get enqueued_jobs.'''
    # if euid is -1, dumps everything
    # TODO: Anything more creative (and robust)?
    if euid == -1:
        return enqueued_jobs
    # _check_perm(euid)
    return enqueued_jobs.get(euid, {})


def remove_job(euid, job_id):
    '''Remove a job from enqueued_jobs based on job ID.'''
    # _check_perm(euid)
    jobs = get_enqueued_jobs(euid)
    try:
        del jobs[job_id]
    except KeyError:
        write_file(
            DAEMON_LOG,
            'Removal failed: No such job with ID {} for UID {}'
            .format(job_id, euid),
            mode='at'
        )
            
        
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
    def __init__(self, euid, exact, command, time_, use_shell=False,
                 job_id=None):
        self.euid = int(euid)
        # Checking Permission
        # _check_perm(self.euid)
        # job_id is sent by runner when updating a Job params
        if job_id:
            job = enqueued_jobs[self.euid][job_id]
            self.job_id = job_id
            # Hmmm...future thinking scope
            self.exact = exact
            self.command = job['command'] if command == '_' \
                else command
            if time_ == '_':
                self.date_time_epoch = job['job_run_at']
            else:
                self.time_str = time_
                self.date_time_epoch = self.get_run_at_epoch()
            self.use_shell = job['use_shell'] if use_shell == '_' \
                else use_shell
            # use_shell is absent: removing shell reference from command
            if not self.use_shell and not use_shell == '_':
                self.command = re.sub(r'^\S+\s+-c\s+"(.*)"$', r'\1',
                                      self.command)
                
        else:
            self.command = command
            self.use_shell = use_shell
            self.exact = exact
            self.time_str = time_
            self.date_time_epoch = self.get_run_at_epoch()
            # Saving the job, with the user's EUID as keys, and increasing
            # IDs as subdict keys with command, time, use_shell as values
            self.job_id = self._get_job_id()
            
        if not self.date_time_epoch:
            return
        enqueued_jobs[self.euid].update({
            self.job_id: {
                'command': self.command,
                'job_run_at': int(self.date_time_epoch),  # to int
                'use_shell': self.use_shell,
                'exact': self.exact,
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
        write_file(
            DAEMON_LOG,
            'Job slot exceeded: Maximum {} jobs can be enqueued'
            .format(max_id),
            mode='at'
        )
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
                self.date_time_epoch = time.mktime(self.date_time.timetuple())
                # Taking a margin of 2 secs so that time
                # spec like `now` works
                if self.date_time_epoch < time.time() - 2:
                    raise HatTimerException(
                        'No backward time travel support: {}'
                        .format(self.time_str))
                return self.date_time_epoch
        if not self.date_time:
            raise HatTimerException(('Ambiguous input time: {}'
                                     '. Please see the help page.')
                                    .format(self.time_str))

    def __repr__(self):
        return 'Hat Job: <{}>at<{}>'.format(self.command,
                                            self.time_str)

    
if __name__ == '__main__':
    pass

