import os
from contextlib import contextmanager

import fcntl

@contextmanager
def file_lock(lock_file):
    with open(lock_file, 'w') as fd:
        fcntl.lockf(fd, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.lockf(fd, fcntl.LOCK_UN)
    os.remove(lock_file)