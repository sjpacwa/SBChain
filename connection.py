"""
connection.py

This file is responsible for storing the class that is responsible for 
socket-based network communication.
"""

from math import ceil
from socket import socket, AF_INET, SOCK_STREAM
import json


class ConnectionHandler():
	"""
	Connection Handler
	"""

	def __init__(self, host, port, buffer_size=256):
		self.host = host
		self.port = port

		self.BUFFER_SIZE = buffer_size

		self.sock = socket(AF_INET, SOCK_STREAM)
		self.sock.connect((self.host, self.port))

	def _send(self, data):
		data_size = len(data)

		self.sock.send(str(data_size).encode())
		test = self.sock.recv(16).decode()
		print(test)
		self.sock.send(data)

	def _get_datagram_size(self, connection):
		"""
		_get_datagram_size
		This function will listen on the connection for the size of the 
		future datagram.

		:param connection: The new connection.

		:return: (data size, number of buffer cycles needed)
		"""

		data_size = int(self.sock.recv(16).decode())

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
			data += self.sock.recv(self.BUFFER_SIZE).decode()

		return json.loads(data[:data_size])

	def send_with_response(self, data):
		data = data.encode()

		self._send(data)
		data_size, num_buffers = self._get_datagram_size(self.sock)
		data = self._get_datagram(self.sock, data_size, num_buffers)
		
		return data

	def send_wout_response(self, data):
		data = data.encode()

		self._send(data)

#conn = ConnectionHandler('127.0.0.1', 5000)

#send_data = '{"name":"test", "args": {"message": "test2"} }'

#data = conn.send_with_response(send_data)

#print(data)