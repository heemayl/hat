'''Miscellaneous utilities.'''

import fcntl
import os
import time


class FLock:
    '''A context manager for exclusive locking (LOCK_EX) of files.'''
    def __init__(self, lockfile_suffix=''):
        self.lockfile = os.path.join(os.path.dirname(__file__),
                                     '.lockfile_{}'.format(lockfile_suffix))

    def __enter__(self):
        self.lockf = open(self.lockfile, 'w')
        while True:
            try:
                fcntl.lockf(self.lockf, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                time.sleep(0.5)
                continue
            return self.lockf
        
    def __exit__(self, *exc_info):
        fcntl.lockf(self.lockf, fcntl.LOCK_UN)
        self.lockf.close()
