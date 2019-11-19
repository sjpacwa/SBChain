"""
main.py

This file is responsible for parsing the command line arguments and 
starting the Flask webserver for the node.
"""

# Standard Library Imports
from argparse import ArgumentParser
import logging
from network import NetworkHandler

# Local Imports
from api import app

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
	last_block = node.blockchain.last_block
	proof = node.blockchain.proof_of_work(last_block)

	# A reward is provided for a successful proof. This is marked as a 
	# newly minted coin by setting the sender to '0'.
	network_handler.node.blockchain.new_transaction(
		sender='0',
		recipient=node.identifier,
		amount=1,
		timestamp=datetime.now()
	)

	# Create the new block and add it to the end of the chain.
	block = node.blockchain.new_block(proof, last_block.hash())

	network_handler._dispatch(RECEIVE_BLOCK(block.toDict()))

	# Generate a response to report that block creation was successful.
	response = {
		'message': "New block mined.",
		'index': block.index,
		'transactions': block.transactions,
		'proof': block.proof,
		'previous_hash': block.previous_hash
	}
	logging.info(json.dumps(block.toDict()))

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
	nh.event_loop()

	
