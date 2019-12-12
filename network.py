"""
network.py

This file is responsible for storing the class that is responsible for 
the socket-based main network loop.
"""

from math import ceil
from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread, Lock
import json
import logging
from datetime import datetime
import hashlib
#import os
#import sys

# Local Imports
from node import Node
from block import Block
from connection import SingleConnectionHandler
from macros import *
from threads import *

class NetworkHandler():
	"""
	Network Handler
	"""

	def __init__(self, host, port, buffer_size=256):
		"""
		__init__
		Constructor for the NetworkHandler class.

		:param host: The IP address that the socket should be bound to.
		:param port: The port that the socket should be bound to.
		:param thread_functions: A dictionary that allows a Thread to 
			lookup a function object with a function name.
		:param buffer_size: The size of the buffer used in data 
			transmission.
		"""

		self.host = host
		self.port = port

		self.T_FUNCTIONS = THREAD_FUNCTIONS
		self.BUFFER_SIZE = buffer_size

		self.node = Node()
		self.active_lock = Lock()
		self.active = True

	def isActive(self):
		status = ""
		self.active_lock.acquire()
		status = self.active
		self.active_lock.release()
		return status
	def setActive(self,status):
		self.active_lock.acquire()
		self.active_lock = status
		self.active_lock.release()

	def register_nodes(self,peers):
		"""
		register_nodes

		Public.
		This function handles a POST request to /nodes/register. It 
		registers a peer with the node.
		"""
		# Check that something was sent.
		if peers is None:
			print("Error: No nodes supplied")
			return

		# Register the nodes that have been received.
		for peer in peers:
			if peer[0] != self.host and peer[1] != self.port:
				self.node.register_node(peer.address,peer.port)

		# Generate a response to report that the peer was registered.

		logging.info(NODES(list(self.node.nodes)))

	def consensus(self):
		"""
		consensus

		Public.
		This function handles a GET request to /nodes/resolve. It checks
		if the chain needs to be updated.
		"""

		# TODO See what the standard is for this in bitcoin.

		replaced = self.node.resolve_conflicts()

		# Based on conflicts, generate a response of which chain is valid.
		if replaced:
			logging.info(REPLACED(self.node.blockchain.get_chain()))
		else:
			logging.info(AUTHORITATIVE(self.node.blockchain.get_chain()))

	def event_loop(self):
		"""
		event_loop
		This function will setup the socket and wait for incoming 
		connections.
		"""

		logging.info("Setting up socket and binding to %s:%s", self.host, 
			self.port)
		self.sock = socket(AF_INET, SOCK_STREAM)
		self.sock.bind((self.host, self.port))

		# Block while waiting for connections.
		while self.isActive():
			logging.info('Waiting for new connections')
			self.sock.listen(1)

			connection, client = self.sock.accept()
			logging.info('Created connection to %s:%s', client[0], 
				client[1])

			data_size, num_buffers = self._get_data_size(connection)
			data = self._get_data(connection, data_size, num_buffers)

			self._dispatch_thread(connection, data)

	def _get_data_size(self, connection):
		"""
		_get_data_size
		This function will listen on the connection for the size of the 
		future data.

		:param connection: The new connection.

		:return: (data size, number of buffer cycles needed)
		"""

		data_size = int(connection.recv(16).decode())
		connection.send(b'ACK')

		return (data_size, ceil(data_size / self.BUFFER_SIZE))

	def _get_data(self, connection, data_size, num_buffers):
		"""
		_get_data
		This function will listen on the connection for the data.

		:param connection: The new connection.
		:param data_size: The size of the incoming data.
		:param num_buffers: The number of buffer cycles required.

		:return: JSON representation of the data.
		"""

		data = ''
		for i in range(num_buffers):
			data += connection.recv(self.BUFFER_SIZE).decode()

		return json.loads(data[:data_size])

	def _dispatch_thread(self, connection, data):
		"""
		_dispatch_thread
		This function will dispatch a worker thread to handle the 
		request.

		:param connection: The new connection.
		:param data: JSON representation of the data.
		"""

		try:
			function_name = data['name']
			function_args = data['args']

			logging.info('Dispatching function %s', function_name)

			th = Thread(target=self.T_FUNCTIONS[function_name], args=(connection, function_args,))
			th.start()
		except:
			logging.error(data)
			self.setActive(False)


