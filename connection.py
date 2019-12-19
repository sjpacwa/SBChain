"""
connection.py

This file is responsible for storing the class that is responsible for 
socket-based network communication.
"""

from math import ceil
from socket import socket, AF_INET, SOCK_STREAM
import json
import logging
from blockchain import config

class SingleConnectionHandler():
	"""
	Single Connection Handler
	"""

	def __init__(self, host, port, buffer_size=256):
		self.host = host
		self.port = port

		self.BUFFER_SIZE = int(buffer_size)

		self.sock = socket(AF_INET, SOCK_STREAM)
	
	def socket_connect(self):
		try:
			self.sock.connect((self.host, self.port))
			return True
		except:
			return False


	def _send(self, data):
		logging.debug("Sending data (single_connection_handler)")
		logging.debug("Data:")
		logging.debug(data)
		data_size = len(data)
		logging.debug("Data size:")
		logging.debug(data_size)

		self.sock.send(str(data_size).encode())
		test = self.sock.recv(16).decode()
		logging.debug(test)
		self.sock.send(data)

	def _get_data_size(self, connection):
		"""
		_get_data_size
		This function will listen on the connection for the size of the 
		future data.

		:param connection: The new connection.

		:return: (data size, number of buffer cycles needed)
		"""

		data_size = int(self.sock.recv(16).decode())

		#logging.debug("Buffer Size Type {}".format(type(self.BUFFER_SIZE)))

		return (data_size, ceil(data_size / self.BUFFER_SIZE))

	def _get_data(self, connection, data_size, num_buffers):
		"""
		_get_data
		This function will listen on the connection for the data.

		:param connection: The new connection.
		:param data_size: The size of the incoming datagram.
		:param num_buffers: The number of buffer cycles required.

		:return: JSON representation of the data.
		"""

		data = ''
		for i in range(num_buffers):
			data += self.sock.recv(self.BUFFER_SIZE).decode()

		return json.loads(data[:data_size])

	def send_with_response(self, data):
		data = json.dumps(data, indent=4, sort_keys=True, default=str).encode()
		self._send(data)
		data_size, num_buffers = self._get_data_size(self.sock)
		data = self._get_data(self.sock, data_size, num_buffers)

		return data

	def send_wout_response(self, data):
		# Data receieved is a dictionary
		data = json.dumps(data, indent=4, sort_keys=True, default=str).encode()
		logging.debug("Sending w/o response")
		self._send(data)
		
