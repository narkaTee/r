import tempfile
import os

working_path = os.path.join(tempfile.gettempdir(), 'r')

def get_named_path(name):
    return os.path.join(working_path, name)