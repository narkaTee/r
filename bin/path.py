import tempfile
import os

tempdir = tempfile.gettempdir()
tempdir_segment = 'r_v4'


def create_temp_path():
    p = get_temp_path()
    if not os.path.exists(p):
        os.makedirs(p)


def get_temp_path():
    p = os.path.join(tempdir, tempdir_segment)
    #if not os.path.exists(p):
    #    os.makedirs(p)
    return p


def get_named_path(name):
    return os.path.join(get_temp_path(), name)