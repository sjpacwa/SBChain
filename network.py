"""
network.py

This file is responsible for storing the class that is responsible for 
socket-based network communication.
"""

from math import ceil
from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread
import json
import logging


class NetworkHandler():
	"""
	Network Handler
	"""

	def __init__(self, host, port, thread_functions, buffer_size=256):
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

		self.T_FUNCTIONS = thread_functions
		self.BUFFER_SIZE = buffer_size

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
		while True:
			logging.info('Waiting for new connections')
			self.sock.listen(1)

			connection, client = self.sock.accept()
			logging.info('Created connection to %s:%s', client[0], 
				client[1])

			data_size, num_buffers = self._get_datagram_size(connection)
			data = self._get_datagram(connection, data_size, num_buffers)

			self._dispatch_thread(connection, data)

	def _get_datagram_size(self, connection):
		"""
		_get_datagram_size
		This function will listen on the connection for the size of the 
		future datagram.

		:param connection: The new connection.

		:return: (data size, number of buffer cycles needed)
		"""

		data_size = int(connection.recv(16))

		return (data_size, ceil(data_size / self.BUFFER_SIZE))

	def _get_datagram(self, connection, data_size, num_buffers):
		"""
		_get_datagram
		This function will listen on the connection for the datagram.

		:param connection: The new connection.
		:param data_size: The size of the incoming datagram.
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

		function_name = data['name']
		function_args = data['args']

		logging.info('Dispatching function %s', function_name)

		th = Thread(target=self._test, args=(connection, function_args,))
		th.start()

	def _test(self, connection, arguments):
		"""
		_test
		This function should only be used to test functionality of the 
		dispatcher.

		:param connection: The new connection.
		:param arguments: JSON representation of the arguments.
		"""
		logging.info('Message: %s', arguments['message'])
		connection.close()

