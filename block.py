import hashlib
import json
from time import time


class Block:
	def __init__(self,index,transactons,proof,previous_hash):
		self.index = index
		self.timestamp = time()
		self.transactions = transactions
		self.proof = proof	
		self.previous_hash = previous_hash
		
	@staticmethod
	def hash(self):
		"""
		Creates a SHA-256 hash of a Block

		:param block: Block
		"""
		block = {
			'index': self.index,
			'timestamp': self.timestamp,
			'transactions': self.transactions,
			'proof': self.proof,
			'previous_hash': self.previous_hash,
		}

		# We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
		block_string = json.dumps(block, sort_keys=True).encode()
		return hashlib.sha256(block_string).hexdigest()

