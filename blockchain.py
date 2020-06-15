"""
blockchain.py

This file defines the Blockchain class which is used to manage information 
related to the chain.
"""

# Standard library imports
import hashlib
import json
import logging
from datetime import datetime

# Local imports
from block import Block
from blockchainConfig import BlockchainConfig
from encoder import ComplexEncoder

config = BlockchainConfig()


class Blockchain:
    """
    Blockchain
    """

    def __init__(self):
        """
        __init__()
    
        The constructor for a Blockchain object.
        """

        self.current_transactions = []
        self.chain = []

        # The version number is incremented in resolve conflicts and is returned 
        # in paginated get chain.
        self.version_number = 0

        # Create the genesis block
        self.new_block(previous_hash='1', proof=100, date=datetime.min.strftime('%Y-%m-%dT%H:%M:%SZ'))

    def get_chain(self):
        """
        get_chain()

        Returns the entire chain of mined blocks.

        :return: <list> list of json representation of chain
        """

        json_chain = []

        for block in self.chain:
            json_chain.append(block.to_json())
            
        return json_chain

    def new_block(self, proof, previous_hash, date=datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')):
        """
        new_block()

        Create a new block and add it the end of the blockchain

        :param proof: <int> The proof given by the Proof of Work algorithm
        :param previous_hash: <str> Hash of previous Block
        
        :return: <Block Object> New Block
        """

        block = Block(len(self.chain)+1,self.current_transactions,proof,previous_hash or self.chain[-1].hash,date)

        # Reset the current list of transactions
        self.current_transactions = []

        self.chain.append(block)
        logging.info(block.to_json())

        return block

    def add_block(self, block):
        """
        add_block()

        Adds an already created block to the end of the blockchain. For example
        a block off the network.

        :param block: <Block Object> The block to add.
        """

        self.chain.append(block)
        logging.info(block.to_json())

    def new_transaction(self, transaction):
        """
        new_transaction()

        Adds an already created transaction to the current transactions list.

        :param transaction: <Transaction Object> The transaction to add.

        :return: <int> The index of the Block that will hold this transaction.
        """

        self.current_transactions.append(transaction)
        logging.info(self.current_transactions[-1].to_string())

        return self.last_block.index + 1

    def update_reward(self, reward_transaction):
        """
        update_reward()

        Adds the reward transaction to the current transactions list when 
        starting to mine.

        :param reward_transaction: <RewardTransaction Object> The transaction
            to add
        """

        if len(self.current_transactions) == 0:
            self.current_transactions.append(reward_transaction)
        else:
            self.current_transactions[0] = reward_transaction

    @property
    def last_block(self):
        """
        last_block()

        Returns the last block in the chain.

        :return: <Block Object> The last block in the chain.
        """

        return self.chain[-1]

    @property
    def last_block_index(self):
        """
        last_block_index()

        Returns the index of the last block in the chain.

        :return: <int> The index of the last block.
        """

        return self.chain[-1].index

    def get_block(self, index):
        """
        get_block()

        Returns the block in the chain at a given index.

        :return: <Block Object> The block object at the index or None if 
            it does not exist.
        """
        
        try:
            return self.chain[index - 1]
        except IndexError:
            return None

    @staticmethod
    def valid_proof(last_proof, proof, last_hash, current_transactions):
        """
        valid_proof()

        Validates the proof of work for a new block.

        :param last_proof: <int> The previous block's proof.
        :param proof: <int> The proof of the block being checked.
        :param last_hash: <str> The hash of the previous block.
        :param current_transactions: <list<Transaction>> A list of current 
            transactions.

        :return: <bool> True if correct, False if not.
        """

        transactions = json.dumps(current_transactions, cls=ComplexEncoder)

        guess = f'{last_proof}{proof}{last_hash}{transactions}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        
        # This is where difficulty is set.
        difficulty = config.get_block_difficulty()
        return guess_hash[:difficulty] == '0' * difficulty

    def get_version_number(self):
        """
        get_version_number()

        Returns the version number that is used to track major changes to 
        the blockchain.

        :return: <int> The current version number of the blockchain.
        """

        return self.version_number

    def increment_version_number(self):
        """
        increment_version_number()

        Increments the version number by one. This should be done when major
        changes occur in the blockchain.
        """

        self.version_number += 1

