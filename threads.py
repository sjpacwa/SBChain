from connection import SingleConnectionHandler
from multicast import MulticastHandler

def receive_block(self, connection,arguments):
	"""
	receive_block

	Internal.
	This function handles a POST request to /block/receive_block. It 
	receives a block from a peer and forwards it along to everyone but 
	the original sender.
	"""
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
			return 

		else:
			# The proof is not valid and the block is ignored and not 
			# propogated.
			logging.info("Bad Proof")
			return 


def new_transaction(self, connection, arguments):
	"""
	new_transaction

	Public.
	This function handles a POST request to /transactions/new. It 
	creates a new transaction and adds it to the pool of transactions.
	"""
	
	# NOTE: Currently, all transactions are considered valid. This 
	# means that 'fake' transactions will be added as well.
	
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
	MulticastHandler(self.peers).multicast_wout_response(RECEIVE_TRANSACTION(transaction))

	logging.info(TRANSACTION_ADDED(block_index))


def receive_transactions(self,connection,arguments):
	"""
	receive_transaction

	Internal.
	This function handles a POST request to /transactions/receive_transaction. 
	It receives a transaction from a peer and forwards it along to everyone 
	but the original sender.
	"""

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


def full_chain(self,connection,arguments):
	"""
	full_chain

	Public.
	This function handles a GET request to /chain. It returns a copy of 
	the entire chain.
	"""

	# TODO This needs to reply to the socket that is passed, it does not communicate to any other nodes, just returns local chain on socket.

	# Assemble the chain for the response.
	return CHAIN(self.node.blockchain.get_chain(),len(self.node.blockchain.get_chain()))

def get_block(self,connection,arguments):
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


