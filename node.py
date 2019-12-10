"""
node.py
This file defines the Node class which is used to store information node 
specific information.
"""

# Standard library imports
import json
from urllib.parse import urlparse
from uuid import uuid4

# Local imports
from blockchain import Blockchain
from block import Block


class Node:
	def __init__(self):
		self.nodes = set()
		self.blockchain = Blockchain()
		self.identifier = str(uuid4()).replace('-', '')

	def resolve_conflicts(self):
		"""
		This is our consensus algorithm, it resolves conflicts
		by replacing our chain with the longest one in the network.

		:return: True if our chain was replaced, False if not
		"""

		neighbors = self.nodes
		our_chain = self.blockchain.chain
		replace_chain = None

		# We're only looking for chains longer than ours
		our_length = len(our_chain)

		# Grab and verify the chains from all the nodes in our network
		for node in neighbors:
			# TODO Change to new connections.
			# Should be handled by connection.py.
			response = request_response(node)

			if "Error" not in response:
				response = json.dumps(response)
				neighbor_length = response['length']
				neighbor_chain = response['chain']

				# Check if the neighbors chain is longer and if it is valid.
				if (neighbor_length > our_length 
					and self.blockchain.valid_chain(neighbor_chain)):
					our_length = neighbor_length
					replace_chain = ""
					for block in neighbor_chain:
						replace_chain.append(Block(block['index'], block['transactions'], block['proof'], block['previous_hash'], block['timestamp']))

		# Replace our chain if we discovered a new, valid chain longer than ours
		if replace_chain:
			our_chain = replace_chain
			return True

		return False

	def register_node(self, address,port):
		"""
		Add a new node to the list of nodes

		:param address: Address of node. Eg. 'http://192.168.0.5:5000'

		NOTE: We assume that nodes don't drop later in the blockchain's lifespan
		"""

		parsed_url = urlparse(address)
		if parsed_url.netloc:
			self.nodes.add((parsed_url.netloc,port))
		elif parsed_url.path:
			# Accepts an URL without scheme like '192.168.0.5:5000'.
			self.nodes.add((parsed_url.path,port))
		else:
			raise ValueError('Invalid URL')
