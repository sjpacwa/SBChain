"""
connection.py

This file is responsible for storing the class that is responsible for 
socket-based network communication.
"""

from socket import socket, AF_INET, SOCK_STREAM


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

		self.sock.send(data_size)
		self.sock.send(data)

	def send_with_response(self, data):
		self._send(data)

		# Get the length of the incoming datagram.
		# Calculate the number of 'buffer frames'
		# Receive response
		# Return response

	def send_wout_response(self, data):
		self._send(data)