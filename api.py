"""
api.py

This file is responsible for defining the API that is used to interact 
with a node. It also provides functionality for nodes to communicate 
with each other to automatically distribute info.
"""

# Standard Library Imports
from datetime import datetime
import hashlib
import json
import logging
import os
import sys

# Third Party Imports
from flask import Flask, jsonify, request

# Local Imports
from node import Node
from block import Block

# Instantiate the Flask webserver.
app = Flask(__name__)

# Instatiate the local node.
node = Node()


@app.route('/mine', methods=['GET'])
def mine():
	"""
	mine

	This function handles a GET request to /mine. It creates a new 
	block with a valid proof and add it to the end of the blockchain. 
	This block is then propogated to the node's peers.
	"""

	# Get a valid proof of work for the last block in the chain.
	last_block = node.blockchain.last_block
	proof = node.blockchain.proof_of_work(last_block)

	# A reward is provided for a successful proof. This is marked as a 
	# newly minted coin by setting the sender to '0'.
	node.blockchain.new_transaction(
		sender='0',
		recipient=node.identifier,
		amount=1,
		timestamp=datetime.now(),
		port=os.environ['FLASK_PORT']
	)

	# Create the new block and add it to the end of the chain.
	block = node.blockchain.new_block(proof, last_block.hash())

	# Prepare for broadcasting to peers.
	target = 'http://{}/block/receive_block'
	headers = {
		'Content-type': 'application/json',
		'Accept': 'text/plain'
	}
	data = {
		**block.toDict(),
		'port': os.environ['FLASK_PORT']
	}

	# Broadcast the message to peers. The response is ignored, because
	# no further action is taken by this node.
	for peer in node.nodes:
		address = target.format(peer)
		requests.post(address, data=json.dumps(data, indent=4, sort_keys=True, 
			default=str), headers=headers)

	# Generate a response to report that block creation was successful.
	response = {
		'message': "New block mined.",
		'index': block.index,
		'transactions': block.transactions,
		'proof': block.proof,
		'previous_hash': block.previous_hash
	}
	
	return jsonify(response), 201


@app.route('/block/receive_block', methods=['POST'])
def receive_block():
	"""
	receive_block

	This function handles a POST request to /block/receive_block. It 
	receives a block from a peer and forwards it along to everyone but 
	the original sender.
	"""

	# Extract the values from the request.
	values = request.get_json()

	# Create a block from the sent data.
	new_block = Block(
		values['index'],
		values['transactions'],
		values['proof'],
		values['previous_hash'],
		values['timestamp']
	)
	
	# Ensure that this block has not been added before.
	for block in node.blockchain.chain:
		if new_block == block:
			return jsonify({'message': 'Duplicate block.'}), 200

	else:
		# The block has not been added before. The proof should be 
		# checked.
		last_proof = node.blockchain.last_block.proof
		last_hash = node.blockchain.last_block.hash()
		proof = values['proof']
		transactions = values['transactions']

		# Remove the reward from the block. If it is kept in, the proof 
		# will not be the same.
		block_reward = None
		for transaction in transactions:
			if transaction['sender'] == '0':
				block_reward = transaction
				break
		transactions.remove(block_reward)

		if node.blockchain.valid_proof(last_proof, proof, last_hash, 
			transactions):
			# The proof is valid and the block can be added. The reward 
			# transaction should be returned.
			transactions.append(block_reward)

			# Clear the pool of the transactions that are present in 
			# the mined block.
			for i in range(len(node.blockchain.current_transactions)):
				for item in transcations:
					if node.blockchain.current_transactions[i] == item:
						node.blockchain.current_transactions.remove(
							node.blockchain.current_transactions[i])

			# Append the block to the chain.
			node.blockchain.chain.append(new_block)
			node.blockchain.chain_dict.append(new_block.toDict())

			# Prepare for broadcasting to peers.
			target = 'http://{}/block/receive_block'
			headers = {
				'Content-type': 'application/json',
				'Accept': 'text/plain'
			}
			data = {
				**block.toDict(),
				'port': os.environ['FLASK_PORT']
			}

			# Broadcast the message to peers except for the original 
			# sender. The response is ignored, because no further 
			# action is taken by this node.
			sender = request.environ['REMOTE_ADDR'] + ':' + values['port']
			for peer in node.nodes:
				if peer != sender:
					address = target.format(peer)
					requests.post(address, data=json.dumps(data, indent=4, 
						sort_keys=True, default=str), headers=headers)

			return jsonify({'message': 'Block added.'}), 201

		else:
			# The proof is not valid and the block is ignored and not 
			# propogated.
			return jsonify({'message': 'Bad proof.'}), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
	"""
	new_transaction

	This function handles a POST request to /transactions/new. It 
	creates a new transaction and adds it to the pool of transactions.
	"""
	
	# NOTE: Currently, all transactions are considered valid. This 
	# means that 'fake' transactions will be added as well.

	# Extract the values from the request.
	data = request.get_json()

	# Ensure that the required values are in the request.
	required = ['sender', 'recipient', 'amount']
	if not all(k in data for k in required):
		return jsonify({'message': 'Missing values.'}), 400

	# Add the current time and the node's port to the values.
	data['timestamp'] = datetime.now()
	data['port'] = os.environ['FLASK_PORT']

	# Create a new transaction from received data.
	block_index = node.blockchain.new_transaction(
		sender=data['sender'],
		recipient=data['recipient'],
		amount=data['amount'],
		timestamp=data['timestamp'],
		port=data['port']
	)

	# Prepare for broadcasting to peers.
	target = 'http://{}/transactions/receive_transactions'
	headers = {
		'Content-type': 'application/json',
		'Accept': 'text/plain'
	}

	# Broadcast the message to peers. The response is ignored, because
	# no further action is taken by this node.
	for peer in node.nodes:
		address = target.format(peer)
		requests.post(address, data=json.dumps(data, indent=4, sort_keys=True, 
			default=str), headers=headers)

	# Generate a response to report that transaction creation was successful.
	response = {
		'message': 'Transaction will be added to block {}.'.format(block_index)
	}

	return jsonify(response), 201


@app.route('/transactions/receive_transactions', methods=['POST'])
def receive_transactions():
	"""
	receive_transaction

	This function handles a POST request to /transactions/receive_transaction. 
	It receives a transaction from a peer and forwards it along to everyone 
	but the original sender.
	"""

	# Extract the values from the request.
	values = request.get_json()

	# Create a new transaction.
	transaction = {
		'sender': values.get('sender'),
		'recipient': values.get('recipient'),
		'amount': values.get('amount'),
		'timestamp': values.get('timestamp'),
		'port': values.get('port')
	}

	# Compute the hash of the transaction for comparison.
	transaction_hash = hashlib.sha256(json.dumps(transaction).encode())
	
	# Make sure that the transaction doesn't match a previous one.
	for node_transaction in node.blockchain.current_transactions:
		node_transaction_hash = hashlib.sha256(node_transaction)
		if node_transaction_hash == transaction_hash:
			return jsonify({'message': 'Duplicate transaction.'}), 200

	else:
		# The transaction was not found. Add to the pool.
		node.blockchain.new_transaction(
			sender=transaction['sender'],
			recipient=transaction['recipient'],
			amount=transaction['amount'],
			timestamp=transaction['timestamp'],
			port=transaction['port']
		)

		# Prepare for broadcasting to peers.
		target = 'http://{}/transaction/receive_transaction'
		headers = {
			'Content-type': 'application/json',
			'Accept': 'text/plain'
		}
		data = transaction

		# Broadcast the message to peers except for the original 
		# sender. The response is ignored, because no further 
		# action is taken by this node.
		sender = request.environ['REMOTE_ADDR'] + ':' + values['port']
		for peer in node.nodes:
			if peer != sender:
				address = target.format(peer)
				requests.post(address, data=json.dumps(data, indent=4, 
					sort_keys=True, default=str), headers=headers)

		return jsonify({'message': 'Transaction added.'}), 201


@app.route('/chain', methods=['GET'])
def full_chain():
	"""
	full_chain

	This function handles a GET request to /chain. It returns a copy of 
	the entire chain.
	"""

	# Assemble the chain for the response.
	response = {
		'chain': node.blockchain.chain_dict,
		'length': len(node.blockchain.chain_dict)
	}
	
	return jsonify(response), 200


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
	"""
	register_nodes

	This function handles a POST request to /nodes/register. It 
	registers a peer with the node.
	"""

	# Extract the values from the request.
	values = request.get_json()

	# Check that something was sent.
	if values is None:
		return jsonify({'message': 'No nodes supplied.'}), 400

	# Retrieve the list of addresses from nodes.
	nodes = values.get('nodes')

	# Register the nodes that have been received.
	for peer in nodes:
		node.register_node(peer)

	# Generate a response to report that the peer was registered.
	response = {
		'message': 'Nodes added to peer list.',
		'total_nodes': list(node.nodes)
	}

	return jsonify(response), 201


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
	"""
	consensus

	This function handles a GET request to /nodes/resolve. It checks
	if the chain needs to be updated.
	"""

	replaced = node.resolve_conflicts()

	# Based on conflicts, generate a response of which chain is valid.
	if replaced:
		response = {
			'message': 'Our chain was replaced.',
			'new_chain': node.blockchain.chain_dict
		}
	else:
		response = {
			'message': 'Our chain is authoritative.',
			'chain': node.blockchain.chain_dict
		}

	return jsonify(response), 200
