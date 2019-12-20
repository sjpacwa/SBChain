"""
block.py
This file defines the Block class which is used to hold information on the 
blocks that are stored in the blockchain.
"""

# Standard library imports
import hashlib
import json
from datetime import datetime
import logging

class Block:
	def __init__(self, index, transactions, proof, previous_hash, timestamp=-1):
		"""
		Constructor
		"""

		self.index = index
		self.transactions = transactions
		self.proof = proof
		self.previous_hash = previous_hash
		self.timestamp = datetime.min if timestamp == -1 else timestamp

	def to_json(self):
		return {
			'index': self.index,
			'transactions': self.transactions,
			'proof': self.proof,
			'previous_hash': self.previous_hash,
			# TODO See how timestamps are handled.
			'timestamp': self.timestamp
		}

	def hash(self):
		"""
		Creates a SHA-256 hash of a Block

		:param block: Block
		"""
		logging.debug("Hash function")
		# We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
		# TODO Verify if sorting is necessary.
		block_string = json.dumps(self.to_json(), indent=4, sort_keys=True, default=str).encode()

		logging.debug(block_string)

		return hashlib.sha256(block_string).hexdigest()

	def __eq__(self, other):
		"""
		Equal Operator
		"""
		return (self.index == other.index
			and self.timestamp == other.timestamp
			and self.transactions == other.transactions
			and self.proof == other.proof
			and self.previous_hash == other.previous_hash)

 

