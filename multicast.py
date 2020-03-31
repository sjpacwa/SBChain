"""
multicast.py

This file is responsible for multicast
socket-based network communication.
"""

# Standard Library Imports
from math import ceil
from socket import socket, AF_INET, SOCK_STREAM
import json
import logging

# Local Imports
from connection import SingleConnectionHandler

class MulticastHandler():
	"""
	Multicast Handler
	"""
	def __init__(self, peers, buffer_size=256):
		logging.debug("Multicast INIT")
		logging.debug("Peers:")
		logging.debug(peers)
		self.buffer_size = int(buffer_size)
		self.peers = peers
		self.peer_connections = []
		for peer in self.peers:
			con = SingleConnectionHandler(peer[0],peer[1],self.buffer_size)
			if con.socket_connect():
				self.peer_connections.append(con)

	def multicast_with_response(self, data):
		peer_response = []
			
		for peer_connection in self.peer_connections:
			response = peer_connection.send_with_response(data)
			# can't index by class or socket
			peer_response.append(response)

		return peer_response

	def multicast_wout_response(self, data):
		logging.debug("Multicast w/o response")
		logging.debug("Peer Connections:")
		logging.debug(self.peer_connections)
		for peer_connection in self.peer_connections:
			peer_connection.send_wout_response(data)
