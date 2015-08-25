#import os
from contextlib import contextmanager
import r_portalocker

locked_files = set()

@contextmanager
def file_lock(lock_file):
    if lock_file in locked_files:
        yield
    else:
        with open(lock_file, 'w') as fd:
            r_portalocker.lock(fd, r_portalocker.LOCK_EX)
            locked_files.add(lock_file)
            try:
                yield
            finally:
                r_portalocker.unlock(fd)
                locked_files.remove(lock_file)
    #os.remove(lock_file)