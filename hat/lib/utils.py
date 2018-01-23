'''Miscellaneous utilities.'''

import datetime
import fcntl
import json
import os
import time


class FLock:
    '''A context manager for exclusive locking (LOCK_EX) of files.'''
    def __init__(self, lockfile_prefix=''):
        self.lockfile = os.path.join(os.path.dirname(__file__),
                                     '._{}.lock'.format(lockfile_prefix))

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
        

def print_msg(msg, flush_stream=True):
    '''Wrapper for formatting-printing.'''
    print('\n{}\n'.format(msg), end='\n', flush=flush_stream)
    return


def read_file(file_path, mode='rt', whole=False, json_loads=False):
    '''Reading from a file with FLock; if `whole` is True, reads
    whole content, otherwise just a single line. `json_load`
    parameter dictates the output format.
    '''
    lock_name = 'read_{}'.format(file_path.replace('/', '_'))
    with FLock(lock_name):
        with open(file_path, mode) as f:
            try:
                content = f.read() if whole else next(f)
            except (EOFError, StopIteration):
                return None
            return json.loads(content.strip()) if json_loads else content


def write_file(file_path, content, mode='wt', nodate=False, json_dumps=False):
    '''Writes `content` to `filename`. Similar design to `read_file`'''
    lock_name = 'write_{}'.format(file_path.replace('/', '_'))
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
            
        
if __name__ == '__main__':
    pass
