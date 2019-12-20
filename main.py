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

	# Remove the reward from the block. If it is kept in, the proof 
	# will not be the same.
	block_reward = None
	for transaction in last_block.transactions:
		if transaction['sender'] == '0':
			block_reward = transaction
			break
	if block_reward:
		last_block.transactions.remove(block_reward)

	#TODO potential problem where receieving transactions during/after proof is set, undefined behavior?
	# I.E proof created with missing transactions
	#my_transactions = network_handler.node.blockchain.current_transactions
	proof = network_handler.node.blockchain.proof_of_work(last_block)

	# A reward is provided for a successful proof. This is marked as a 
	# newly minted coin by setting the sender to '0'.
	network_handler.node.blockchain.new_transaction(
		sender='0',
		recipient=network_handler.node.identifier,
		amount=1,
		timestamp=datetime.now()
	)

	# add back reward
	if block_reward:
		last_block.transactions.append(block_reward)

	# Create the new block and add it to the end of the chain.
	block = network_handler.node.blockchain.new_block(proof, last_block.hash())
	logging.debug("Mine peers:")
	logging.debug(network_handler.node.nodes)
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
	logging.debug("Response:")
	logging.debug(json.dumps(block.to_json(), indent=4, sort_keys=True, default=str))
	# Reset Transactions


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
	parser.add_argument('--debug',default = False,action='store_true')	
	args = parser.parse_args()
	port = args.port
	ip = args.ip

	if args.debug:
		logging.basicConfig(level=logging.DEBUG)
	else:
		logging.basicConfig(level=logging.INFO)

	nh = NetworkHandler(ip, port)

	# TODO decide who gets to register nodes, might need a centralized source that returns a random set of nodes to be neighbors
	nh.register_nodes(NEIGHBORS)
	th = Thread(target=mine_loop, args=(nh,))
	th.start()
	nh.event_loop()


	
