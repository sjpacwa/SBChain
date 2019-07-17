"""
api.py

This file is responsible for defining the API that is used for interacting with
the node server as well as providing a way for peers to communicate with each
other.
"""

# Standard Library Imports
import logging
import requests
import json
import hashlib
import sys

# Third Party Imports
from flask import Flask, jsonify, request
from aiohttp import web,ClientSession

# Local Imports
from node import Node

# Instantiate the local node Flask webserver.
app = Flask(__name__)

# Instatiate the node that this server represents.
node = Node()

@app.route('/mine', methods=['GET'])
def mine():
	"""
	mine
	This function handles a GET request to 0.0.0.0/mine. It will create a new 
	block with a proof of concept and add it to the blockchain.
	"""

	logging.info(
		'Received API call "/mine". Generating a valid proof of work.'
	)

	# Run the proof of work algorithm to get a valid proof.
	last_block = node.blockchain.last_block
	proof = node.blockchain.proof_of_work(last_block)
	logging.info(
		'Valid proof of work generated based on previous block {}.'.format(
			last_block.index
		)
	)

	# Due to successful mining of the block, a reward is provided. A sender of
	# "0" designates that this is a new coin.
	node.blockchain.new_transaction(
		sender='0',
		recipient=node.identifier,
		amount=1
	)
	logging.info(
		'New transaction added to block due to valid proof of work.'
	)

	# Create the new block and add it to the end of the chain.
	previous_block_hash = last_block.hash()
	block = node.blockchain.new_block(proof, previous_block_hash)
	logging.info(
		'New block created and added to the end of the block.'
	)

	# TODO Broadcast the newly created block to peers. Stephen
	# Sender: Send the new block to peer.
	# Peer: Validate the new block and add to chain. Forward to other peers.

	# Generate a response to report that block creation was successful.
	response = {
		'message': "New block forged.",
		'index': block.index,
		'transactions': block.transactions,
		'proof': block.proof,
		'previous_hash': block.previous_hash,
	}
	
	return jsonify(response), 200

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
	"""
	new_transaction
	This function handles a POST request to 0.0.0.0/transactions/new. It will
	create a new transaction and add it to the pool of transactions.
	"""

	logging.info(
		'Received API call "/transactions/new". Adding transcation to pool.'
	)

	# Get the values from the request as JSON.
	values = request.get_json()

	# Check that all required fields are in the POST data.
	required = ['sender', 'recipient', 'amount']
	if not all(k in values for k in required):
		logging.warn('Received data did not include a required field.')
		return 'Error: Missing values', 400

	# Create a new transaction from received data.
	block_index = node.blockchain.new_transaction(
		sender=values['sender'],
		recipient=values['recipient'],
		amount=values['amount']
	)

	# TODO Broadcast the transaction that was received to peers. Daniel
	# Sender: Send the new transaction to peer.
	# Peer: If not duplicate, add transaction to list and forward to other 
	# peers.

	#we never use node.peers for anything ?

	msgs = []
	# TODO add timestamp in transaction + send hash
	for peer in node.nodes:
		trnx_msg = broadcast_transaction(peer,values)
		logging.warn(trnx_msg)
		print(trnx_msg)

	# Generate a response to report that the transaction was added to pool.
	response = {
		'message': 'Transaction will be added to block {}.'.format(block_index),
	}
	response['msgs'] = msgs

	return jsonify(response), 201

def broadcast_transaction(peer,transaction):
	"""
	broadcast_transaction
	This function broadcasts a transaction that was recieved to peers
	"""

	#logging.basicConfig(filename="debug.log",filemode='w')
	endpoint = 'http://' + str(peer) + "/transactions/recieve_transaction"

	#logging.warn(endpoint)

	r = requests.post(url=endpoint,data=transaction)

	return r

@app.route('/transactions/recieve_transaction', methods=['GET'])
def recieve_transactions():
	values = request.get_json()

	transaction = values.get('transaction')
	trnx_hash = hashlib.sha256(json.dumps(transaction))
	#check if transaction is a duplicate
	for my_trnx in node.blockchain.current_transactions:
		# if duplicate, ignore
		my_hash = hashlib.sha256(my_trnx)
		if my_hash == trnx_hash:
			response = {
				'msg' : 'Recieved duplicate transaction {}'.format(node.identifier)
			}

			#app.logger.warn(response)

			return jsonify(response), 200
	else:
		app.logger.info(
			'Recieved a new transaction, adding to current_transactions'
		)
		node.blockchain.new_transaction(transaction['sender'],transaction['recipient'],transaction['amount'],transaction['timestamp'])
		
		#broadcast transaction
		for peer in node.nodes:
			broadcast_transaction(peer,transaction)

		return jsonify(transaction), 200


@app.route('/chain', methods=['GET'])
def full_chain():
	"""
	full_chain
	This function handles a GET request to 0.0.0.0/chain. It will return a copy
	of the entire chain.
	"""

	logging.info(
		'Received API call "/chain". Returning a copy of the blockchain.'
	)

	# Assemble the chain for the response.
	response = {
		'chain': node.blockchain.chain_dict,
		'length': len(node.blockchain.chain_dict),
	}
	
	return jsonify(response), 200

@app.route('/nodes/register', methods=['POST'])
def register_nodes():
	"""
	register_nodes
	This function handles a POST request to 0.0.0.0/nodes/register. It will 
	register a peer with the node.
	"""

	logging.info(
		'Received API call "/nodes/register". Adding peer to node\'s peer list.'
	)

	# Get the values from the request as JSON.
	values = request.get_json()

	if values is None:
		logging.warn('Did not receive a node list.')
		return "Error: Please supply a valid list of nodes", 400
	# Retrieve the list of addresses from nodes.
	nodes = values.get('nodes')

	# Register the nodes that have been received.
	for item in nodes:
		node.register_node(item)

	# Generate a response to report that the transaction was added to pool.
	response = {
		'message': 'New nodes have been added to peer list.',
		'total_nodes': list(node.nodes),
	}

	return jsonify(response), 201

@app.route('/nodes/resolve', methods=['GET'])
def consensus():
	"""
	consensus
	This function handles a GET request to 0.0.0.0/nodes/resolve. It will 
	determine if the local chain is behind.
	"""

	logging.info(
		'Received API call "/nodes/resolve". Checking if our list is valid.'
	)

	# TODO this needs to be returned to original algorithm. Daniel
	replaced = resolve_conflicts(node.blockchain)

	# Based on conflicts, generate a response of which chain was valid.
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
