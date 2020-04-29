"""
thread.py

This file is responsible for defining several classes that are used to 
manage the threads that perform work.
"""

# Standard library imports
from queue import Queue
from threading import Thread

# Local imports
from macros import BUFFER_SIZE
from mine import Miner
from tasks import *

class Worker(Thread):
    """
    Worker
    """

    def __init__(self, metadata, queues):
        Thread.__init__(self)
        self.metadata = metadata
        self.queues = queues
        self.daemon = True
        self.start()

    def run(self):
        while True:
            func, args, kwargs, conn = self.queues['tasks'].get()

            try:
                func(*args, self.metadata, self.queues, conn, **kwargs)
            except Exception as e:
                print(e)
            finally:
                self.queues['tasks'].task_done()
                conn.close()


class ThreadHandler():
    """
    ThreadHandler
    """

    def __init__(self, metadata, num_threads):
        self.queues = {}
        self.queues['tasks'] = Queue()
        self.queues['trans'] = Queue()
        self.queues['blocks'] = Queue()
        for _ in range(num_threads):
            Worker(metadata, self.queues)

        if not metadata['debug']:
            Miner(metadata, self.queues)

    def add_task(self, task, conn):
        # TODO Add some stuff to detect errors.

        action = THREAD_FUNCTIONS[task['action']]
        params = task['params']

        self.queues['tasks'].put((action, params, {}, conn))

