#import os
from contextlib import contextmanager
import portalocker

@contextmanager
def file_lock(lock_file):
    with open(lock_file, 'w') as fd:
        portalocker.lock(fd, portalocker.LOCK_EX)
        try:
            yield
        finally:
            portalocker.unlock(fd)
    #os.remove(lock_file)