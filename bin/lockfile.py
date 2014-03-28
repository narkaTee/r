#import os
from contextlib import contextmanager
import portalocker

locked_files = set()

@contextmanager
def file_lock(lock_file):
    if lock_file in locked_files:
        yield
    else:
        with open(lock_file, 'w') as fd:
            portalocker.lock(fd, portalocker.LOCK_EX)
            locked_files.add(lock_file)
            try:
                yield
            finally:
                portalocker.unlock(fd)
                locked_files.remove(lock_file)
    #os.remove(lock_file)