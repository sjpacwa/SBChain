"""
node.py

This file defines the Node class which is used to store node specific
information.

2020 Stephen Pacwa and Daniel Okazaki
Santa Clara University
"""

# Standard library imports
from uuid import uuid4

# Local imports
from blockchain import Blockchain
from history import History
from logger import initialize_log
from network import NetworkHandler
from threading import Lock


class Node:
    """
    Node
    """

    def __init__(self, host, port, initialized=None, uuid=None, debug=False, no_mine=False, benchmark=False, neighbors=[]):
        """
        __init__

        The constructor for a Node object.

        :param host: <str> The ip/host that the node should use.
        :param port: <int> The port that the node should use.
        :param initialized: <Semaphore> Semaphore that can be used to test if node has finished setting up.
        :param uuid: <str> The UUID the node should use.
        :param debug: <boolean> Whether the node should be started in debug mode.
        :param no_mine: <boolean> Whether or not the node should allow mining to occur.
        :param benchmark: <boolean> Whether or not the node should start in benchmark mode.
        :param neighbors: <list> The neighbors the node should be initialized with.
        """

        self.metadata = {}
        self.metadata['done'] = initialized
        self.metadata['host'] = host
        self.metadata['port'] = port
        self.metadata['uuid'] = str(uuid4()).replace('-', '') if uuid is None else uuid
        self.metadata['debug'] = debug
        self.metadata['no_mine'] = no_mine
        self.metadata['benchmark'] = benchmark
        self.metadata['resolve_requests'] = set()
        self.metadata['resolve_lock'] = Lock()

        if benchmark:
            from threading import Semaphore
            self.metadata['benchmark_lock'] = Semaphore(0)

        if self.metadata['uuid'] == 'SYSTEM':
            raise InvalidID

        initialize_log(self.metadata['uuid'], debug)

        # Create the Blockchain object.
        self.metadata['blockchain'] = Blockchain()
        self.metadata['history'] = History(self.metadata['uuid'])

        # Create the Network Handler object.
        self.nh = NetworkHandler(self.metadata, neighbors)

        # Start the Network Handler main loop.
        self.nh.event_loop()


class InvalidID(Exception):
    """
    InvalidID

    A dummy exception to throw when an ID is passed that is not allowed.
    """
    pass
