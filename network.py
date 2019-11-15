"""
network.py

This file is responsible for storing the class that is responsible for 
the socket-based main network loop.
"""

from math import ceil
from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread
import json
import logging
from datetime import datetime
import hashlib
#import os
#import sys

# Local Imports
from node import Node
from block import Block
from connection import ConnectionHandler
from macros import *

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

		data_size = int(connection.recv(16).decode())
		connection.send(b'ACK')

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

		try:
			function_name = data['name']
			function_args = data['args']

			logging.info('Dispatching function %s', function_name)

			th = Thread(target=self.T_FUNCTIONS['function_name'], args=(connection, function_args,))
			th.start()
		except:
			logging.error(data)

	def broadcast(self,connection,arguments):
		"""
		broadcast
		This function will send information to an already established connection. 
		No response is expected

		:param connection: The new connection.
		:param arguments: data to be sent to the receiver
		"""
		connection.send(len(arguments))
		connection.send(arguments)
	
	def broadcast_all(self,connection,arguments):
		"""
		broadcast_all
		This function will establish a connection and send information to ALL peers

		:param arguments: data to be sent to the receiver
		"""
		for peer in self.node.nodes:
			if peer.address != self.host and peer.port != self.port:
				p_address = peer[0]
				p_port = peer[1]
				# TODO Socket abstraction so that we don't have to deal with sockets in api.py
				conn = ConnectionHandler(p_address,p_port)
				conn.send_wout_response(arguments)

	def request_result(self,peer,arguments):
		# Requesting data from peer.
		p_address = arguments['host']
		p_port = arguments['port']
		conn = ConnectionHandler(p_address,p_port)

		data = arguments['args']
		return conn.send_with_response(data)

	def receive_block(self, connection,arguments):
		"""
		receive_block

		Internal.
		This function handles a POST request to /block/receive_block. It 
		receives a block from a peer and forwards it along to everyone but 
		the original sender.
		"""
		# Create a block from the sent data.
		new_block = Block(
			index=arguments['index'],
			transactions=arguments['transactions'],
			proof=arguments['proof'],
			previous_hash=arguments['previous_hash'],
			timestamp=arguments['timestamp']
		)
		
		# Ensure that this block has not been added before.
		for block in self.node.blockchain.chain:
			if new_block == block:
				logging.info("Duplicate Block")
				return

		else:
			# The block has not been added before. The proof should be 
			# checked.
			last_proof = self.node.blockchain.last_block.proof
			last_hash = self.node.blockchain.last_block.hash()

			# Remove the reward from the block. If it is kept in, the proof 
			# will not be the same.
			block_reward = None
			for transaction in arguments['transactions']:
				if transaction['sender'] == '0':
					block_reward = transaction
					break
			arguments['transactions'].remove(block_reward)

			if self.node.blockchain.valid_proof(last_proof, arguments['proof'], last_hash, 
				arguments['transactions']):
				# The proof is valid and the block can be added. The reward 
				# transaction should be returned.
				arguments['transactions'].append(block_reward)

				# Clear the pool of the transactions that are present in 
				# the mined block.
				for i in range(len(self.node.blockchain.current_transactions)):
					for item in arguments['transactions']:
						if self.node.blockchain.current_transactions[i] == item:
							self.node.blockchain.current_transactions.remove(
								self.node.blockchain.current_transactions[i])

				# Append the block to the chain.
				self.node.blockchain.chain.append(new_block)


				self._dispatch_thread(connection,BROADCAST_ALL_RECEIVE_BLOCK(new_block.toDict()))

				logging.info("Block Added")
				return 

			else:
				# The proof is not valid and the block is ignored and not 
				# propogated.
				logging.info("Bad Proof")
				return 

	def new_transaction(self, connection, arguments):
		"""
		new_transaction

		Public.
		This function handles a POST request to /transactions/new. It 
		creates a new transaction and adds it to the pool of transactions.
		"""
		
		# NOTE: Currently, all transactions are considered valid. This 
		# means that 'fake' transactions will be added as well.
		
		timestamp = datetime.now()
		transaction = TRANSACTION(arguments['sender'],arguments['recipient'],arguments['amount'],timestamp)

		# Create a new transaction from received data.
		block_index = self.node.blockchain.new_transaction(
			sender=arguments['sender'],
			recipient=arguments['recipient'],
			amount=arguments['amount'],
			timestamp=timestamp
		)

		self._dispatch_thread(connection,BROADCAST_ALL_RECEIVE_TRANSACTION(transaction))

		logging.info(TRANSACTION_ADDED(block_index))

	def receive_transactions(self,connection,arguments):
		"""
		receive_transaction

		Internal.
		This function handles a POST request to /transactions/receive_transaction. 
		It receives a transaction from a peer and forwards it along to everyone 
		but the original sender.
		"""

		# Create a new transaction.
		transaction = TRANSACTION(arguments['sender'],arguments['recipient'],arguments['amount'],arguments['timestamp'])
		# Compute the hash of the transaction for comparison.
		transaction_hash = hashlib.sha256(json.dumps(transaction).encode())
		
		# Make sure that the transaction doesn't match a previous one.
		for node_transaction in self.node.blockchain.current_transactions:
			node_transaction_hash = hashlib.sha256(node_transaction)
			if node_transaction_hash == transaction_hash:
				logging.info("Duplicate Transaction")

		else:
			# The transaction was not found. Add to the pool.
			self.node.blockchain.new_transaction(
				sender=arguments['sender'],
				recipient=arguments['recipient'],
				amount=arguments['amount'],
				timestamp=arguments['timestamp']
			)

			self._dispatch_thread(connection,BROADCAST_ALL_RECEIVE_TRANSACTION(transaction))

			logging.info("Transaction added")
	
	def full_chain(self,connection,arguments):
		"""
		full_chain

		Public.
		This function handles a GET request to /chain. It returns a copy of 
		the entire chain.
		"""

		# Assemble the chain for the response.
		if connection:
			self._dispatch_thread(connection,CHAIN(self.node.blockchain.get_chain(),len(self.node.blockchain.get_chain())))
		else:	
			logging.info(CHAIN(self.node.blockchain.get_chain(),len(self.node.blockchain.get_chain())))

	
	def register_nodes(self,connection,arguments):
		"""
		register_nodes

		Public.
		This function handles a POST request to /nodes/register. It 
		registers a peer with the node.
		"""
		nodes = arguments['nodes']
		# Check that something was sent.
		if nodes is None:
			print("Error: No nodes supplied")
			return

		# Register the nodes that have been received.
		for peer in nodes:
			self.node.register_node(peer.address,peer.port)

		# Generate a response to report that the peer was registered.

		logging.info(NODES(list(self.node.nodes)))

	def consensus(self,connection,arguments):
		"""
		consensus

		Public.
		This function handles a GET request to /nodes/resolve. It checks
		if the chain needs to be updated.
		"""

		replaced = self.node.resolve_conflicts()

		# Based on conflicts, generate a response of which chain is valid.
		if replaced:
			logging.info(REPLACED(self.node.blockchain.get_chain()))
		else:
			logging.info(AUTHORITATIVE(self.node.blockchain.get_chain()))
	
	def get_block(self,connection,arguments):
		"""
		get_block

		Public.
		This function handles a GET request to /block/get_block. It returns 
		the block that has been requested.
		"""

		# Check that something was sent.
		if arguments['values'] is None:
			self._dispatch_thread(connection,NO_INDEX_FOUND)
			return

		block = self.node.blockchain.get_block(arguments['values'].get('index'))

		if block is -1:
			self._dispatch_thread(connection,INVALID_INDEX)
		else:
			self._dispatch_thread(connection,BLOCK_RECEIVED(block.index,block.transactions,block.proof,block.previous_hash))