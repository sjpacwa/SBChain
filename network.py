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
from macros import *
from threads import *
from blockchain import config
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

		self.T_FUNCTIONS = self.THREAD_FUNCTIONS
		self.BUFFER_SIZE = int(buffer_size)

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
		self.active = status
		self.active_lock.release()

	def register_nodes(self,peers):
		"""
		register_nodes

		Public.
		This function handles a POST request to /nodes/register. It 
		registers a peer with the node.
		"""
		# Check that something was sent.
		logging.debug("Registering Nodes")
		logging.debug(peers)
		if peers is None:
			print("Error: No nodes supplied")
			return

		# Register the nodes that have been received.
		for peer in peers:
			logging.debug("Peer")
			logging.debug(peer)
			if peer[0] != self.host or peer[1] != self.port:
				logging.debug("Registering Node")
				self.node.register_node(peer[0],peer[1])

		# Generate a response to report that the peer was registered.

		#logging.info(NODES(list(self.node.nodes)))

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
			logging.info("------------------------------------------------------------------------------------------------------------------------")
			logging.info("REPLACED")
			#logging.info(REPLACED(self.node.blockchain.get_chain()))
			logging.info("------------------------------------------------------------------------------------------------------------------------")

		else:
			logging.info("------------------------------------------------------------------------------------------------------------------------")
			#logging.info(AUTHORITATIVE(self.node.blockchain.get_chain()))
			logging.info("authoritative")
			logging.info("------------------------------------------------------------------------------------------------------------------------")


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
		logging.info("Data size received:")
		logging.info(data_size)
		connection.send(b'ACK')
		
		logging.info("Buffer Size Type {}".format(type(self.BUFFER_SIZE)))

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
		
		logging.info("Data Receieved")
		logging.info(data)

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
			if not function_args:
				th = Thread(target=self.T_FUNCTIONS[function_name], args=(self,connection,))
				th.start()
			else:
				th = Thread(target=self.T_FUNCTIONS[function_name], args=(self,connection,function_args,))
				th.start()
		except:
			logging.error(data)
			self.setActive(False)

	def receive_block(self, connection,arguments):
		"""
		receive_block

		Internal.
		This function handles a POST request to /block/receive_block. It 
		receives a block from a peer and forwards it along to everyone but 
		the original sender.
		"""
		logging.info("Received Block (from dispatcher) with Block Number: {}".format(arguments['index']))
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


				# TODO This should be done with multicast.
				MulticastHandler(self.peers).multicast_wout_response(BROADCAST_ALL_RECEIVE_BLOCK(new_block.to_json()))

				logging.info("Block Added")

			else:
				# The proof is not valid and the block is ignored and not 
				# propogated.
				logging.info("Bad Proof")
				


	def new_transaction(self, connection, arguments):
		"""
		new_transaction

		Public.
		This function handles a POST request to /transactions/new. It 
		creates a new transaction and adds it to the pool of transactions.
		"""
		
		# NOTE: Currently, all transactions are considered valid. This 
		# means that 'fake' transactions will be added as well.
		
		logging.info("Creating new transaction (from dispatcher)")
		timestamp = datetime.now()
		transaction = TRANSACTION(arguments['sender'],arguments['recipient'],arguments['amount'],timestamp)

		# Create a new transaction from received data.
		block_index = self.node.blockchain.new_transaction(
			sender=arguments['sender'],
			recipient=arguments['recipient'],
			amount=arguments['amount'],
			timestamp=timestamp
		)

		# TODO This should be done with multicast.
		MulticastHandler(self.peers).multicast_connect().multicast_wout_response(RECEIVE_TRANSACTION(transaction))

		#logging.info(TRANSACTION_ADDED(block_index))


	def receive_transactions(self,connection,arguments):
		"""
		receive_transaction

		Internal.
		This function handles a POST request to /transactions/receive_transaction. 
		It receives a transaction from a peer and forwards it along to everyone 
		but the original sender.
		"""
		logging.info("Received transaction (from dispatcher)")

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

			# TODO This should be done with multicast.
			MulticastHandler(self.peers).multicast_wout_response(RECEIVE_TRANSACTION(transaction))
			logging.info("Transaction added")


	def full_chain(self,connection):
		logging.info("Received full_chain request (from dispatcher)")
		"""
		full_chain

		Public.
		This function handles a GET request to /chain. It returns a copy of 
		the entire chain.
		"""

		# TODO This needs to reply to the socket that is passed, it does not communicate to any other nodes, just returns local chain on socket.

		# Assemble the chain for the response.
		chain = CHAIN(self.node.blockchain.get_chain(),len(self.node.blockchain.get_chain()))
		chain = json.dumps(chain, indent=4, sort_keys=True, default=str).encode()
		data_len = len(chain)
		connection.send(str(data_len).encode())
		connection.send(b'ACK')
		connection.send(chain)

	def get_block(self,connection,arguments):
		
		logging.info("Received get block request (from dispatcher)")

		"""
		get_block

		Public.
		This function handles a GET request to /block/get_block. It returns 
		the block that has been requested.
		"""

		# TODO Just need to respond to the connection.

		# Check that something was sent.
		if arguments['values'] is None:
			self._dispatch_thread(connection,NO_INDEX_FOUND)
			return

		block = self.node.blockchain.get_block(arguments['values'].get('index'))

		return BLOCK_RECEIVED(block.index,block.transactions,block.proof,block.previous_hash)

	THREAD_FUNCTIONS = {
		"receive_block": receive_block,
		"new_transaction": new_transaction,
		"receieve_transactions": receive_transactions,
		"full_chain": full_chain,
		"get_block": get_block
	}





