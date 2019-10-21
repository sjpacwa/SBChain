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

# Local Imports
from node import Node
from block import Block
from main import ip, port

# Instatiate the local node.
node = Node()

def broadcast(name, args):
	# Prepare for broadcasting to peers.
	data = {
		'name': name,
		'args': args
	}
	# Broadcast the message to peers. The response is ignored, because
	# no further action is taken by this node.
	for peer in node.nodes:
		if peer.address != ip and per.port != port
			address = peer['address']
			port = peer['port']
			# TODO Socket abstraction so that we don't have to deal with sockets in api.py
			send(data,address,port)

def mine():
	"""
	mine

	Public.
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
		timestamp=datetime.now()
	)

	# Create the new block and add it to the end of the chain.
	block = node.blockchain.new_block(proof, last_block.hash())

	thread = threading.Thread(target=broadcast,args=('receive_transaction',json.dumps(block.toDict()), ))
	thread.start()

	# Generate a response to report that block creation was successful.
	response = {
		'message': "New block mined.",
		'index': block.index,
		'transactions': block.transactions,
		'proof': block.proof,
		'previous_hash': block.previous_hash
	}
	print(json.dumps(response))

def receive_block(index,transactions,proof,previous_hash,timestamp):
	"""
	receive_block

	Internal.
	This function handles a POST request to /block/receive_block. It 
	receives a block from a peer and forwards it along to everyone but 
	the original sender.
	"""

	# Create a block from the sent data.
	new_block = Block(
		index=index,
		transactions=transactions,
		proof=proof,
		previous_hash=previous_hash,
		timestamp=timestamp
	)
	
	# Ensure that this block has not been added before.
	for block in node.blockchain.chain:
		if new_block == block:
			print("Duplicate Block")
			return

	else:
		# The block has not been added before. The proof should be 
		# checked.
		last_proof = node.blockchain.last_block.proof
		last_hash = node.blockchain.last_block.hash()

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
				for item in transactions:
					if node.blockchain.current_transactions[i] == item:
						node.blockchain.current_transactions.remove(
							node.blockchain.current_transactions[i])

			# Append the block to the chain.
			node.blockchain.chain.append(new_block)

			thread = threading.Thread(target=broadcast,args=('receive_block', json.dumps(block.toDict()), ))
			thread.start()
			
			print("Block Added")
			return 

		else:
			# The proof is not valid and the block is ignored and not 
			# propogated.
			print("Bad Proof")
			return 

def new_transaction(sender, recipient, amount):
	"""
	new_transaction

	Public.
	This function handles a POST request to /transactions/new. It 
	creates a new transaction and adds it to the pool of transactions.
	"""
	
	# NOTE: Currently, all transactions are considered valid. This 
	# means that 'fake' transactions will be added as well.

	timstamp = datetime.now()
	# Create a new transaction from received data.
	block_index = node.blockchain.new_transaction(
		sender=sender,
		recipient=recipient,
		amount=amount,
		timestamp=timestamp,
		port=port
	)

	args = {
		'sender': sender,
		'recipient': recipient,
		'amount': amount,
		'timestamp': timestamp,
		'port': port
	}

	thread = threading.Thread(target=broadcast,args=('receive_block',args, ))
	thread.start()

	# Generate a response to report that transaction creation was successful.
	response = {
		'message': 'Transaction will be added to block {}.'.format(block_index)
	}

	print(json.dumps(response))

def receive_transactions(sender, recipient, amount, timestamp):
	"""
	receive_transaction

	Internal.
	This function handles a POST request to /transactions/receive_transaction. 
	It receives a transaction from a peer and forwards it along to everyone 
	but the original sender.
	"""

	# Extract the values from the request.
	values = request.get_json()

	# Create a new transaction.
	transaction = {
		'sender': sender,
		'recipient': recipient,
		'amount': amount,
		'timestamp': timestamp,
		'port': port
	}

	# Compute the hash of the transaction for comparison.
	transaction_hash = hashlib.sha256(json.dumps(transaction).encode())
	
	# Make sure that the transaction doesn't match a previous one.
	for node_transaction in node.blockchain.current_transactions:
		node_transaction_hash = hashlib.sha256(node_transaction)
		if node_transaction_hash == transaction_hash:
			print("Duplicate Transaction")

	else:
		# The transaction was not found. Add to the pool.
		node.blockchain.new_transaction(
			sender=sender,
			recipient=recipient,
			amount=amount,
			timestamp=timestamp,
			port=port
		)

		thread = threading.Thread(target=broadcast,args=('receive_transaction', json.dumps(transaction), ))
		thread.start()

		print("Transaction added")

def full_chain():
	"""
	full_chain

	Public.
	This function handles a GET request to /chain. It returns a copy of 
	the entire chain.
	"""

	# Assemble the chain for the response.
	response = {
		'chain': node.blockchain.get_chain(),
		'length': len(node.blockchain.get_chain())
	}
	
	return jsonify(response), 200


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
	"""
	register_nodes

	Public.
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

	Public.
	This function handles a GET request to /nodes/resolve. It checks
	if the chain needs to be updated.
	"""

	replaced = node.resolve_conflicts()

	# Based on conflicts, generate a response of which chain is valid.
	if replaced:
		response = {
			'message': 'Our chain was replaced.',
			'new_chain': node.blockchain.get_chain()
		}
	else:
		response = {
			'message': 'Our chain is authoritative.',
			'chain': node.blockchain.get_chain()
		}

	return jsonify(response), 200

@app.route('/block/get_block', methods=['POST'])
def get_block():
	"""
	get_block

	Public.
	This function ahdnesl a GET request to /block/get_block. It returns 
	the block that has been requested.
	"""

	# Extract the values from the request.
	values = request.get_json()

	# Check that something was sent.
	if values is None:
		return jsonify({'message': 'No index supplied'}), 400

	block = node.blockhain.get_block(values.get('index'))

	if block is -1:
		return jsonify({'message': 'Invalid index'}), 400
	else:
		response = {
			'message': "Block retrieved.",
			'index': block.index,
			'transactions': block.transactions,
			'proof': block.proof,
			'previous_hash': block.previous_hash
		}
		return jsonify(response), 200
	