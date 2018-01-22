'''Generic scheduling stuffs for all incoming jobs. Other
modules only need to work with `enqueued_jobs` dict.
'''

import collections
import datetime
import time

from abc import ABCMeta


daemon_log = '/home/chayan/stuffs/hat/logs/hat/daemon.log'

# Jobs enqueued to be run
enqueued_jobs = collections.OrderedDict()


def get_enqueued_jobs():
    '''To be called from other modules to get enqueued_jobs.'''
    return enqueued_jobs


def remove_job(job_id):
    '''Remove a job from enqueued_jobs based on hash_.'''
    try:
        del enqueued_jobs[job_id]
    except KeyError:
        with open(daemon_log, 'a') as f:
            f.write('{} : {}\n'.format(
                datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'Removal failed: No such job with ID {}'.format(job_id)
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
    def __init__(self, command, time_, use_shell=False):
        self.command = command
        self.time_str = time_
        self.use_shell = use_shell
        # Getting when to run in Epoch 
        self.date_time_epoch = self.get_run_at_epoch()
        # Saving the job, with increasing IDs as keys for
        # `enqueued_jobs` and command, time, use_shell as values
        self.job_id = self._get_job_id()
        enqueued_jobs[self.job_id] = {
            'command': self.command,
            'job_run_at': int(self.date_time_epoch),  # to int
            'use_shell': self.use_shell,
        }

    def _get_job_id(self):
        '''Get job ID, to be used
        as the Job dict key.
        '''
        # We'll wrap around at 40000
        max_id = 40000
        current_keys = set(enqueued_jobs.keys())
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
            raise HatTimerException('Ambiguous input time: {}'
                                    .format(self.time_str))
        if self.date_time_epoch <= time.time():
            raise HatTimerException('No time travel support: {}'
                                    .format(self.time_str))

    def __repr__(self):
        return 'Hat Job: <{}>at<{}>'.format(self.command,
                                            self.time_str)

    
if __name__ == '__main__':
    pass
