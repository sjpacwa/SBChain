# Standard Library Imports
import logging
from datetime import datetime
from threading import Thread
import json


#local imports
from macros import NEIGHBORS, RECEIVE_BLOCK
from network import NetworkHandler
from multicast import MulticastHandler

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

	logging.debug("Response:")
	logging.debug(json.dumps(block.to_json(), indent=4, sort_keys=True, default=str))

def mine_loop(network_handler):
	while network_handler.isActive():
		th = Thread(target=mine, args=(network_handler,))
		th.start()
		th.join()
