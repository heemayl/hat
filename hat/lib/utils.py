'''Miscellaneous utilities.'''

import datetime
import fcntl
import logging
import json
import os
import time


class FLock:
    '''A context manager for exclusive locking (LOCK_EX) of files.'''
    def __init__(self, lockfile_prefix=''):
        lockfile_prefix = lockfile_prefix.replace('/', '_')
        self.lockfile = os.path.join('/var/run/hatd/locks',
                                     '._{}.lock'.format(lockfile_prefix))

    def __enter__(self):
        self.lockf = open(self.lockfile, 'w')
        try:
            os.chmod(self.lockfile, 0o660)
        except PermissionError:
            pass
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
        

def print_msg(msg, flush_stream=True):
    '''Wrapper for formatting-printing.'''
    print('\n{}\n'.format(msg), end='\n', flush=flush_stream)
    return


def read_file(file_path, mode='rt', whole=False, json_loads=False):
    '''Reading from a file with FLock; if `whole` is True, reads
    whole content, otherwise just a single line. `json_load`
    parameter dictates the output format.
    '''
    lock_name = '{}/read_{}'.format(file_path, file_path.replace('/', '_'))
    with FLock(lock_name):
        with open(file_path, mode) as f:
            try:
                content = f.read() if whole else next(f)
            except (EOFError, StopIteration):
                return None
            return json.loads(content.strip()) if json_loads else content


def write_file(file_path, content, mode='wt', nodate=False, json_dumps=False):
    '''Writes `content` to `filename`. Similar design to `read_file`'''
    # Create intermediate dirs
    os.makedirs(os.path.dirname(file_path), mode=0o755, exist_ok=True)
    lock_name = '{}/write_{}'.format(file_path, file_path.replace('/', '_'))
    with FLock(lock_name):
        with open(file_path, mode) as f:
            f.write('{} : {}\n'.format(
                datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                content,
            )) if not nodate else f.write(
                json.dumps(content) if json_dumps
                else '{}\n'.format(content)
            )
            return True
            

def username_from_euid(euid):
    '''Takes a EUID, and returns the username.'''
    with open('/etc/passwd') as f:
        for line in f:
            line = line.split(':')
            if str(euid) in line:
                return line[0]


def get_logger(logfile='/var/log/hatd/debug.log'):
    # Enable (debug) logging to /var/log/hatd/debug.log
    logger = logging.getLogger('hatd_base_logger')
    
    handler = logging.FileHandler(logfile)
    handler.setFormatter(logging.Formatter('%(asctime)s:: %(message)s'))
    handler.setLevel(logging.DEBUG)

    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    return logger
    
            
if __name__ == '__main__':
    pass
