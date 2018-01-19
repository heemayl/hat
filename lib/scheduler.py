'''Generic scheduling stuffs for all incoming jobs. Other
modules only need to work with `enqueued_jobs` dict.
'''

import collections
import datetime
import itertools
import os
import sys
import subprocess
import time

from abc import ABCMeta


# Jobs enqueued to be run
enqueued_jobs = collections.OrderedDict()


def get_enqueued_jobs():
    '''To be called from other modules to get enqueued_jobs.'''
    return enqueued_jobs


def remove_job(hash_):
    '''Remove a job from enqueued_jobs based on hash_.'''
    del enqueued_jobs[hash_]
    

class HatTimerException(Exception):
    '''Generic exception class for all input timers.'''
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
    def __init__(self, command, time_):
        self.command = command
        self.time_str = time_
        # Getting when to run in Epoch 
        self.get_run_at_epoch()
        # Saving the job, hash of current+job time as key in `enqueued_jobs`,
        # and command, time to run as values
        self.hash_ = self.date_time_epoch + time.time()
        enqueued_jobs[self.hash_] = {
            'command': self.command,
            'job_run_at': int(self.date_time_epoch),  # to int
        }

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
                break
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

