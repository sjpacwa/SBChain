"""
multicast.py

This file is responsible for multicast
socket-based network communication.

This class is a wrapper of Single Connection Handler
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
		"""
        __init__
    
        The constructor for a Multicast object.

        :param peers: <list> List of peers to communicate with
        :param buffer_size: <int> Buffer size used to receieve data through socket (optional) 
        """
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
		"""
		multicast_with_response()

		Not Thread Safe

		Send data to all peers and expect a response from all peers

		:param data: <str> data to send.

		:return: <list> list of JSON representation of the data from each peer.
		"""
		peer_response = []
			
		for peer_connection in self.peer_connections:
			response = peer_connection.send_with_response(data)
			# can't index by class or socket
			peer_response.append(response)

		return peer_response

	def multicast_wout_response(self, data):
		"""
		multicast_wout_response()

		Not Thread Safe

		Send data to all peers and don't expect a response

		:param data: <str> data to send.
		"""
		logging.debug("Multicast w/o response")
		logging.debug("Peer Connections:")
		logging.debug(self.peer_connections)
		for peer_connection in self.peer_connections:
			peer_connection.send_wout_response(data)
