import hashlib
import json
from time import time


class Block:
	def __init__(self,index,transactions,proof,previous_hash, timestamp = -1):
		self.index = index
		self.timestamp = time() if timestamp == -1 else timestamp
		self.transactions = transactions
		self.proof = proof	
		self.previous_hash = previous_hash
		
	def hash(self):
		"""
		Creates a SHA-256 hash of a Block

		:param block: Block
		"""
		block = self.toDict()

		# We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
		block_string = json.dumps(block, sort_keys=True).encode()
		return hashlib.sha256(block_string).hexdigest()

	def toDict(self):
		return {
			'index': self.index,
			'timestamp': self.timestamp,
			'transactions': self.transactions,
			'proof': self.proof,
			'previous_hash': self.previous_hash,
		}
