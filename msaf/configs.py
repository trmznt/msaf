from rhombus.lib.utils import random_string

TEMP_DIR = None
PROC_DIR = None
LIBEXEC_DIR = None

def set_temp_path( fullpath ):
    global TEMP_DIR
    TEMP_DIR = fullpath

def get_temp_path( path = '' ):
    return "%s/%s" % (TEMP_DIR, path)

def set_proc_path( fullpath ):
    global PROC_DIR
    PROC_DIR = fullpath

def get_proc_path( path = None ):
    if path is None:
        path = random_string(8)
    return "%s/%s" % (PROC_DIR, path)

def set_libexec_path( fullpath ):
    global LIBEXEC_PATH
    LIBEXEC_PATH = fullpath

def get_libexec_path( path = '' ):
    return "%s/%s" % (LIBEXEC_PATH, path)


