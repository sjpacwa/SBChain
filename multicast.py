"""
connection.py

This file is responsible for storing the class that is responsible for 
socket-based network communication.
"""

from math import ceil
from socket import socket, AF_INET, SOCK_STREAM
import json
from connection import SingleConnectionHandler


class MulticastHandler():
	"""
	Multicast Handler
	"""

	def __init__(self, peers, buffer_size=256):
		self.peer_connections = []
		for peer in peers:
			self.peer_connections.append(SingleConnectionHandler(peer[0], peer[1], buffer_size))

	def multicast_with_response(self, data):
		peer_response = {}
		
		for peer_connection in self.peer_connections:
			response = peer_connection.send_with_response(data)
			peer_response[peer_connection] = response

		return peer_response

	def multicast_wout_response(self, data):
		for peer_connection in self.peer_connections:
			peer_connection.send_wout_response(data)
