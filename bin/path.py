import tempfile
import os

working_path = os.path.join(tempfile.gettempdir(), 'r_v4')
if not os.path.exists(working_path):
    os.makedirs(working_path)


def get_named_path(name):
    return os.path.join(working_path, name)