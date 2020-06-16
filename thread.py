"""
thread.py

This file is responsible for defining several classes that are used to
manage the threads that perform work.

2020 Stephen Pacwa and Daniel Okazaki
Santa Clara University
"""

# Standard library imports
import traceback
import logging
from queue import Queue
from threading import Thread

# Local imports
from connection import ConnectionHandler
from mine import Miner
from tasks import *


class Worker(Thread):
    """
    Worker
    """

    def __init__(self, metadata, queues):
        """
        __init__()

        Constructor for the thread object.

        :param metadata: <dict> The metadata of the node.
        :param queues: <dict> The queues of the node.
        """

        Thread.__init__(self)
        self.metadata = metadata
        self.queues = queues
        self.daemon = True
        self.start()

    def run(self):
        """
        run()

        The function that is used to start the thread work.
        """

        while True:
            func, args, kwargs, conn = self.queues['tasks'].get()

            try:
                if isinstance(func, str):
                    func = THREAD_FUNCTIONS[func]
                func(*args, self.metadata, self.queues, conn, **kwargs)
            except Exception as e:
                logging.warning("Inside thread: " + str(e))
                traceback.print_exc()
                traceback.print_stack()
                try:
                    ConnectionHandler()._send(conn, 'Error: invalid data')
                except AttributeError:
                    pass
            finally:
                self.queues['tasks'].task_done()
                try:
                    conn.close()
                except AttributeError:
                    pass


class ThreadHandler():
    """
    ThreadHandler
    """

    def __init__(self, metadata, num_threads):
        """
        __init__()

        The constructor for the ThreadHandler object.

        :param metadata: <dict> The metadata for the node.
        :param num_threads: <int> The number of threads to create.
        """

        self.queues = {}
        self.queues['tasks'] = Queue()
        self.queues['trans'] = Queue()
        self.queues['blocks'] = Queue()
        for _ in range(num_threads):
            Worker(metadata, self.queues)

        Miner(metadata, self.queues)

    def add_task(self, task, conn):
        """
        add_task()

        This function adds a task to the task queue to be consumed
        by the worker threads.

        :param task: <dict> The task that has come off the network.
        :param conn: <Connection Object> The socket that the request came
            in on.
        """

        try:
            action = THREAD_FUNCTIONS[task['action']]
            params = task['params']

            self.queues['tasks'].put((action, params, {}, conn))
        except Exception as e:
            ConnectionHandler()._send(conn, 'Error: Bad request')
            logging.warning(e)
            logging.warning(traceback.format_exc())
            logging.warning(''.join(traceback.format_stack()))
            conn.close()