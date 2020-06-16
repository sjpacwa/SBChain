"""
network.py

This file is responsible for storing the class that is responsible for
the socket-based main network loop.

2020 Stephen Pacwa and Daniel Okazaki
Santa Clara University
"""

# Standard library imports
from socket import socket, AF_INET, SOCK_STREAM
import logging

# Local Imports
from connection import ConnectionHandler
from tasks import register_nodes
from thread import ThreadHandler


class NetworkHandler(ConnectionHandler):
    """
    Single Connection Handler
    """

    def __init__(self, metadata, initial_peers, num_threads=10):
        """
        __init__

        The constructor for a NetworkHandler object.

        :param metadata: <dict> The metadata of the node.
        :param initial_peers: <list<tuple<str, int>> A list of initial peers this node should
            be registered with.
        :param num_threads: <int> The number of worker threads to initialize this node with.
        """

        ConnectionHandler.__init__(self)

        self.metadata = metadata
        self.metadata['peers'] = []

        # Automatically register neighbors.
        register_nodes(initial_peers, self.metadata)

        # Set up socket.
        logging.info("Setting up socket and binding to %s:%s", metadata['host'], metadata['port'])
        self.sock = socket(AF_INET, SOCK_STREAM)
        self.sock.bind((self.metadata['host'], self.metadata['port']))

        # Start thread handler.
        self.threads = ThreadHandler(metadata, num_threads)

    def event_loop(self):
        """
        event_loop

        This function will setup the socket and wait for incoming
        connections.
        """

        # Block while waiting for connections.
        if self.metadata['done'] is not None:
            self.metadata['done'].release()

        while True:
            logging.info('Waiting for new connections')
            self.sock.listen(5)
            conn, client = self.sock.accept()
            logging.info('Created connection to %s:%s', client[0], client[1])

            data = self._recv(conn)

            if data is None:
                continue
            else:
                self.threads.add_task(data, conn)
