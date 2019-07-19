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
import os

# Third Party Imports
from flask import Flask, jsonify, request
from aiohttp import web,ClientSession
from datetime import datetime

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
	# NOTE no current way of checking if transactions are valid or not, fake transactions allowed
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

	values['timestamp'] = datetime.now()
	values['port'] = os.environ['FLASK_PORT']
	# Create a new transaction from received data.
	block_index = node.blockchain.new_transaction(
		sender=values['sender'],
		recipient=values['recipient'],
		amount=values['amount'],
		timestamp = values['timestamp'],
		port = values['port']
	)

	# Broadcast the transaction that was received to peers. Daniel
	# Sender: Send the new transaction to peer.
	# Peer: If not duplicate, add transaction to list and forward to other 
	# peers.

	msgs = []
	for peer in node.nodes:
		broadcast_transaction(peer,values)

	# Generate a response to report that the transaction was added to pool.
	response = {
		'message': 'Transaction will be added to block {}.'.format(block_index),
	}
	response['msgs'] = msgs

	return jsonify(response), 201

def broadcast_transaction(peer,transaction):
	"""
	broadcast_transaction
	This function broadcasts a transaction that was received to peers
	"""
	endpoint = 'http://' + str(peer) + "/transactions/receive_transactions"
	headers = {
			'Content-type': 'application/json', 
			'Accept': 'text/plain'
	}

	r = requests.post(url=endpoint,data=json.dumps(transaction, indent = 4, sort_keys = True, default = str),headers=headers)

	return r, 200

@app.route('/transactions/receive_transactions', methods=['POST'])
def receive_transactions():
	values = request.get_json()
	print("RECEIVE TRANSACTION",values)
	transaction = {
		'sender': values.get('sender'),
		'recipient': values.get('recipient'),
		'amount': values.get('amount'),
		'timestamp': values.get('timestamp'),
		'port': values.get('port')
	}

	trnx_hash = hashlib.sha256(json.dumps(transaction).encode())
	#check if transaction is a duplicate
	for my_trnx in node.blockchain.current_transactions:
		my_hash = hashlib.sha256(my_trnx)
		# if duplicate, ignore
		if my_hash == trnx_hash:
			logging.warn( 'Received duplicate transaction {}'.format(node.identifier))
			return "duplicate", 200
	else:
		logging.info(
			'Received a new transaction, adding to current_transactions'
		)
		node.blockchain.new_transaction(transaction['sender'],transaction['recipient'],transaction['amount'],transaction['timestamp'],transaction['port'])
		
		#broadcast transaction
		for peer in node.nodes:
			print("NEW",request.environ['REMOTE_ADDR'] + ":" + transaction['port'])
			print("PEER",peer)
			#TODO what happens if port changes later?
			if peer != request.environ['REMOTE_ADDR'] + ":" + transaction['port']:
				print("Broadcasting!")
				broadcast_transaction(peer,transaction)

		return "new transaction", 200

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
	replaced = node.resolve_conflicts()

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
