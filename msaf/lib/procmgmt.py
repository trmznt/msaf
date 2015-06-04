# this library contains utility to manage external processes
import logging

log = logging.getLogger(__name__)

from concurrent import futures

def create_proc_path():
    while True:
        proc_path = get_proc_path()
        if os.path.exists( proc_path ):
            continue
        os.mkdir( proc_path )
        break
    return proc_path


class ProcUnit(object):

    def __init__(self, proc_id, uid, obj):
        self.proc_id = proc_id
        self.uid = uid
        self.obj = obj
        self.time_queue = None
        self.time_finish = None
        self.status = 'Q'

#
# main process variables

pool = None
procs = {}

class PoolExecuter(futures.ProcessPoolExecutor):

    def __del__(self):
        print("DELETE THIS POOL, HOW?")
        self.__del__()

def init_pool( processes = 2 ):
    global pool
    if pool is None:
        log.info("preparing %d processes" % processes)
        pool = futures.ProcessPoolExecutor(max_workers=processes)
        pool._adjust_process_count()

def submit( func, *args, **kwargs ):
    global pool
    return pool.submit( func, *args, **kwargs )
    


def sigterm_handler_XXX( signum, frame ):
    print("SIGTERM handler")
    _cleanup()


def _cleanup():
    print("_cleanup()")
    global tasks, workers
    for i in range(len(workers)):
        tasks.put( None )
    for w in workers:
        w.join()
        workers.remove(w)


def init_workers_XXX():
    global workers, procs

    if workers:
        _cleanup()

    num_workers = multiprocessing.cpu_count() - 1
    for i in range(num_workers):
        workers.append( Worker(tasks, procs) )

    for w in workers:
        w.start()

    signal.signal( signal.SIGTERM, sigterm_handler )
    atexit.register( _cleanup )


def put_task():
    pass


