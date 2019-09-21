"""
blockchain.py
This file defines the Blockchain class which is used to manage information 
related to the chain.
test push
"""

# Standard library imports
import hashlib
import json

# Local imports
from block import Block


class Blockchain:
	def __init__(self):
		self.current_transactions = []
		self.chain = []

		# Create the genesis block
		self.new_block(previous_hash='1', proof=100)

	def get_chain(self):
		json_chain = []

		for block in self.chain:
			json_chain.append(block.toDict())
			
		return json_chain

	def valid_chain(self, chain):
		"""
		Determine if a given blockchain is valid

		:param chain: A blockchain
		:return: True if valid, False if not
		"""

		last_block = chain[0]
		current_index = 1

		while current_index < len(chain):
			block = chain[current_index]
			
			# TODO Fix printing.
			print(f'{last_block}')
			print(f'{block}')
			print("\n-----------\n")
			
			# Check that the hash of the block is correct
			block_string = json.dumps(last_block, sort_keys=True).encode()
			last_block_hash = hashlib.sha256(block_string).hexdigest()
			if block['previous_hash'] != last_block_hash:
				return False

			# Check that the Proof of Work is correct
			if not self.valid_proof(last_block['proof'], block['proof'], last_block_hash):
				return False

			last_block = block
			current_index += 1

		return True

	def new_block(self, proof, previous_hash):
		"""
		Create a new Block in the Blockchain

		:param proof: The proof given by the Proof of Work algorithm
		:param previous_hash: Hash of previous Block
		:return: New Block
		"""
		
		block = Block(len(self.chain)+1,self.current_transactions,proof,previous_hash or self.chain[-1].hash())

		# Reset the current list of transactions
		self.current_transactions = []

		self.chain.append(block)
		return block

	def new_transaction(self, sender, recipient, amount,timestamp,port):
		"""
		Creates a new transaction to go into the next mined Block

		:param sender: Address of the Sender
		:param recipient: Address of the Recipient
		:param amount: Amount
		:return: The index of the Block that will hold this transaction
		"""
		self.current_transactions.append({
			'sender': sender,
			'recipient': recipient,
			'amount': amount,
			'timestamp': timestamp,
			'port':port
		})

		return self.last_block.index + 1

	@property
	def last_block(self):
		return self.chain[-1]

	def proof_of_work(self, last_block):
		"""
		Simple Proof of Work Algorithm:

		 - Find a number p' such that hash(pp') contains leading 4 zeroes
		 - Where p is the previous proof, and p' is the new proof
		 
		:param last_block: <dict> last Block
		:return: <int>
		"""

		last_proof = last_block.proof
		last_hash = last_block.hash()

		proof = 0
		while self.valid_proof(last_proof, proof, last_hash, self.current_transactions) is False:
			proof += 1

		return proof

	@staticmethod
	def valid_proof(last_proof, proof, last_hash, current_transactions):
		"""
		Validates the Proof

		:param last_proof: <int> Previous Proof
		:param proof: <int> Current Proof
		:param last_hash: <str> The hash of the Previous Block
		:return: <bool> True if correct, False if not.

		"""

		guess = f'{last_proof}{proof}{last_hash}{current_transactions}'.encode()
		guess_hash = hashlib.sha256(guess).hexdigest()
		
		# This is where difficulty is set.
		return guess_hash[:4] == "0000"
