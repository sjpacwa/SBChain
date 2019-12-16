"""
main.py

This file is responsible for parsing the command line arguments and 
starting the Flask webserver for the node.
"""

# Standard Library Imports
from argparse import ArgumentParser
import logging
from threading import Thread
import json

#local imports
from network import NetworkHandler
from multicast import MulticastHandler
from datetime import datetime
from macros import NEIGHBORS, RECEIVE_BLOCK

def mine(network_handler):
	"""
	mine

	Public.
	This function handles a GET request to /mine. It creates a new 
	block with a valid proof and add it to the end of the blockchain. 
	This block is then propogated to the node's peers.
	"""

	#TODO 
	# Get a valid proof of work for the last block in the chain.
	last_block = network_handler.node.blockchain.last_block
	proof = network_handler.node.blockchain.proof_of_work(last_block)

	# A reward is provided for a successful proof. This is marked as a 
	# newly minted coin by setting the sender to '0'.
	network_handler.node.blockchain.new_transaction(
		sender='0',
		recipient=network_handler.node.identifier,
		amount=1,
		timestamp=datetime.now()
	)

	# Create the new block and add it to the end of the chain.
	block = network_handler.node.blockchain.new_block(proof, last_block.hash())

	MulticastHandler(network_handler.node.nodes).multicast_wout_response(RECEIVE_BLOCK(block.to_json()))

	network_handler.consensus()

	# Generate a response to report that block creation was successful.
	response = {
		'message': "New block mined.",
		'index': block.index,
		'transactions': block.transactions,
		'proof': block.proof,
		'previous_hash': block.previous_hash
	}
	logging.info(json.dumps(block.to_json(), indent=4, sort_keys=True, default=str))

def mine_loop(network_handler):
	while network_handler.isActive():
		th = Thread(target=mine, args=(network_handler,))
		th.start()
		th.join()

if __name__ == '__main__':
	# Parse command line arguments.
	parser = ArgumentParser()
	parser.add_argument('-p', '--port', default=5000, type=int, 
		help='port to listen on')
	parser.add_argument('-ip', '--ip', default='localhost', type=str, 
		help='ip to listen on')
	args = parser.parse_args()
	port = args.port
	ip = args.ip

	logging.basicConfig(level=logging.INFO)

	nh = NetworkHandler(ip, port, {})

	nh.register_nodes(NEIGHBORS)
	th = Thread(target=mine_loop, args=(nh,))
	th.start()
	nh.event_loop()


	
