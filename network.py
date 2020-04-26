"""
network.py

This file is responsible for storing the class that is responsible for 
the socket-based main network loop.
"""
# Standard library imports
from math import ceil
from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread, Lock
import json
from datetime import datetime
import hashlib
import logging

# Local Imports
from tasks import register_nodes
from block import Block
from macros import *
from multicast import MulticastHandler
from mine import Miner, mine_loop

class NetworkHandler():
    """
    Single Connection Handler
    """
    def __init__(self, metadata, initial_peers, buffer_size=256):
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

        self.peers = []
        self.metadata['peers'] = self.peers
        
        # TODO remove nodes in future.
        self.nodes = self.peers

        self.metadata = metadata

        self.host = metadata['host']
        self.port = metadata['port']

        # Automatically register neighbors.
        register_nodes(initial_peers, self.metadata)

        self.sock = None

        # TODO Update the thread functions to be supported as original.
        self.T_FUNCTIONS = self.THREAD_FUNCTIONS
        self.BUFFER_SIZE = int(buffer_size)

        self.blockchain = metadata['blockchain']
        self.identifier = metadata['uuid']

        # TODO stop all threads waiting on things, need to send SIGKILL or something.
        self.active_lock = Lock()
        self.active = True

        self.sh = None
        self.open_log = False

        if TEST_MODE:
            self.miner = Miner(self.blockchain, self.identifier, self.nodes)
        else:
            th = Thread(target=mine_loop, args=(self.blockchain, self.identifier, self.nodes,))
            th.start()

    def event_loop(self):
        """
        event_loop

        Not Thread Safe
        
        This function will setup the socket and wait for incoming 
        connections.
        """

        logging.info("Setting up socket and binding to %s:%s", self.host, 
            self.port)
        self.sock = socket(AF_INET, SOCK_STREAM)
        self.sock.bind((self.host, self.port))

        # Block while waiting for connections.
        while 1:
            logging.info('Waiting for new connections')
            self.sock.listen(1)
            connection, client = self.sock.accept()
            logging.info('Created connection to %s:%s', client[0], 
                client[1])
            try:
                data_size, num_buffers = self._get_data_size(connection)
                connection.send(b'ACK')
                data = self._get_data(connection, data_size, num_buffers)

                self._dispatch_thread(connection, data)
            except ValueError:
                logging.error("Receieved invalid data format. Check README for description")
                connection.close()

    def _get_data_size(self, connection):
        """
        _get_data_size()

        Not Thread Safe
        
        This function will listen on the connection for the size of the 
        future data.

        :param connection: <Socket Connection Object> The new connection.
        :returns: <tuple> (data size <int>, number of buffer cycles needed <int>)
        """

        data_size = int(connection.recv(16).decode())
        logging.debug("Data size received:")
        logging.debug(data_size)
        
        logging.debug("Buffer Size Type {}".format(type(self.BUFFER_SIZE)))

        return (data_size, ceil(data_size / self.BUFFER_SIZE))

    def _get_data(self, connection, data_size, num_buffers):
        """
        _get_data()

        Not Thread Safe

        This function will listen on the connection for the data.

        :param connection: <Socket Connection Object> The new connection.
        :param data_size: <int> The size of the incoming data.
        :param num_buffers: <int> The number of buffer cycles required.

        :return: <json> JSON representation of the data.
        """

        data = ''
        for i in range(num_buffers):
            data += connection.recv(self.BUFFER_SIZE).decode()
        
        logging.debug("Data Receieved")
        logging.debug(data)

        return json.loads(data[:data_size])

    def _dispatch_thread(self, connection, data):
        """
        _dispatch_thread()

        Not Thread Safe

        This function will dispatch a worker thread to handle the 
        request.

        :param connection: <Socket Connection Object> The new connection.
        :param data: <json> JSON representation of the request. 
            Contains the name of the function to call and arguments for that function
        """
        function_name = None
        function_args = None
        try:
            function_name = data['name']
            function_args = data['args']

            logging.info('Dispatching function %s', function_name)
            th = Thread(
                target=self.T_FUNCTIONS[function_name],
                 args=(self,connection,) if not function_args else (self,connection, function_args,)
            )
            th.start()
        except Exception as e:
            if not function_args:
                th = Thread(target=self.T_FUNCTIONS[function_name], args=(self,connection,))
                th.start()
            else:
                th = Thread(target=self.T_FUNCTIONS[function_name], args=(self,connection,function_args,))
                th.start()
        except:
            logging.error("ERROR IN DISPATCHER")
            logging.error(data)

