"""
node.py

This file defines the Node class which is used to store node specific 
information.
"""

# Standard library imports
from uuid import uuid4

# Local imports
from blockchain import Blockchain
from logger import initialize_log
from network import NetworkHandler


class Node:
    """
    Node
    """

    def __init__(self, host,port, initialized=None, uuid=None, debug=False, neighbors=[]):
        """
        __init__
        
        The constructor for a Node object.

        :param host: <str> The ip/host that the node should use.
        :param port: <int> The port that the node should use.
        :param debug: <bool> Whether the node should be started in 
            debug mode.
        :param neighbors: <list> The neighbors the node should be 
            initialized with.
        :param uuid: <string> The UUID the node should use.
        """

        self.metadata = {}
        self.metadata['done'] = initialized
        self.metadata['host'] = host
        self.metadata['port'] = port
        self.metadata['uuid'] = str(uuid4()).replace('-', '') if uuid == None else uuid
        self.metadata['debug'] = debug
        
        initialize_log(self.metadata['uuid'], debug)

        # Create the Blockchain object.
        self.metadata['blockchain'] = Blockchain()

        # Create the Network Handler object.
        self.nh = NetworkHandler(self.metadata, neighbors)

        # Start the Network Handler main loop.
        self.nh.event_loop()

