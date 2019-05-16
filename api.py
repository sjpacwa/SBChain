"""
api.py
This file is responsible for defining the API for interacting with the node
server.
"""

# Standard library imports

# Third party imports
from flask import Flask, jsonify, request

# Local imports
from node import Node

# Instantiate the Node
app = Flask(__name__)

node = Node()

@app.route('/mine', methods=['GET'])
def mine():
	# We run the proof of work algorithm to get the next proof...
	last_block = node.blockchain.last_block
	print(last_block.index)
	proof = node.blockchain.proof_of_work(last_block)

	# We must receive a reward for finding the proof.
	# The sender is "0" to signify that this node has mined a new coin.
	node.blockchain.new_transaction(
		sender="0",
		recipient= node.identifier,
		amount=1,
	)

	# Forge the new Block by adding it to the chain
	previous_hash = last_block.hash()
	block = node.blockchain.new_block(proof, previous_hash)

	response = {
		'message': "New Block Forged",
		'index': block.index,
		'transactions': block.transactions,
		'proof': block.proof,
		'previous_hash': block.previous_hash,
	}
	return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
	values = request.get_json()

	# Check that the required fields are in the POST'ed data
	required = ['sender', 'recipient', 'amount']
	if not all(k in values for k in required):
		return 'Missing values', 400

	# Create a new Transaction
	index = node.blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])

	response = {'message': f'Transaction will be added to Block {index}'}
	return jsonify(response), 201


@app.route('/chain', methods=['GET'])
def full_chain():
	response = {
		'chain': node.blockchain.chain_dict,
		'length': len(node.blockchain.chain_dict),
	}
	return jsonify(response), 200


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
	values = request.get_json()

	nodes = values.get('nodes')
	if nodes is None:
		return "Error: Please supply a valid list of nodes", 400

	for item in nodes:
		node.register_node(item)

	response = {
		'message': 'New nodes have been added',
		'total_nodes': list(node.nodes),
	}
	return jsonify(response), 201


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
	replaced = node.resolve_conflicts()

	if replaced:
		response = {
			'message': 'Our chain was replaced',
			'new_chain': node.blockchain.chain_dict
		}
	else:
		response = {
			'message': 'Our chain is authoritative',
			'chain': node.blockchain.chain_dict
		}

	return jsonify(response), 200
