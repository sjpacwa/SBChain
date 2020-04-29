"""
network.py

This file is responsible for storing the class that is responsible for 
the socket-based main network loop.
"""

# Standard library imports
from socket import socket, AF_INET, SOCK_STREAM
import json
import logging

# Local Imports
from tasks import register_nodes
from thread import ThreadHandler
from macros import BUFFER_SIZE

class NetworkHandler():
    """
    Single Connection Handler
    """
    def __init__(self, metadata, initial_peers, num_threads=10):
        """
        __init__
        
        The constructor for a NetworkHandler object.

        :param host: <string> The IP address that the socket should be 
            bound to.
        :param port: <int> The port that the socket should be bound to.
        :param node: <Node Object> Node Object to interface with
        :param log_host: <string> The IP address of the logging interface server to connect to (optional)
        :param log_port: <bool> The port of the logging interface server to connect to (optional)
        :param buffer_size: <int> The size of the buffer used in data 
            transmission.
        """

        self.metadata = metadata
        self.metadata['peers'] = [] 
        
        # Automatically register neighbors.
        register_nodes(initial_peers, self.metadata)

        # Set up socket.
        logging.info("Setting up socket and binding to %s:%s", metadata['host'], 
            metadata['port'])
        self.sock = socket(AF_INET, SOCK_STREAM)
        self.sock.bind((self.metadata['host'], self.metadata['port']))

        # Start thread handler.
        self.threads = ThreadHandler(metadata, num_threads);

    def event_loop(self):
        """
        event_loop

        Not Thread Safe
        
        This function will setup the socket and wait for incoming 
        connections.
        """

        # Block while waiting for connections.
        while True:
            logging.info('Waiting for new connections')
            self.sock.listen(5)
            conn, client = self.sock.accept()
            logging.info('Created connection to %s:%s', client[0], 
                client[1])

            data = self._get_data(conn)

            if data is None:
                continue
            else:
                self.threads.add_task(data, conn)

    def _get_data(self, conn):
        """
        _get_data()

        Not Thread Safe

        This function will listen on the connection for the data.

        :param connection: <Socket Connection Object> The new connection.
        :param data_size: <int> The size of the incoming data.
        :param num_buffers: <int> The number of buffer cycles required.

        :return: <json> JSON representation of the data.
        """

        try:
            initial_message = conn.recv(BUFFER_SIZE).decode()
            print(initial_message)
            size, data = initial_message.split('~')

            size = int(size)
            amount_received = len(data)
            while amount_received < size:
                data += conn.recv(BUFFER_SIZE).decode()
                amount_received = len(data)

            return json.loads(data[:size])
        except OSError as E:
            # A timeout has occured.
            conn.close()
            return None

