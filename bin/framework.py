import os
import config

def is_installed():
    path = config.get_r_path()
    return os.path.exists(path)


def get_path():
    path = config.get_r_path()
    return path