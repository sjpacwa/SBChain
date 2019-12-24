"""
blockchain.py
This file defines the Blockchain class which is used to manage information 
related to the chain.
test push
"""

# Standard library imports
import hashlib
import json
import logging
from datetime import datetime
# Local imports
from block import Block, block_from_json
from blockchainConfig import BlockchainConfig

config = BlockchainConfig()


class Blockchain:
    def __init__(self):
        self.current_transactions = []
        self.chain = []


        # Create the genesis block
        self.new_block(previous_hash='1', proof=100)

    def get_chain(self):
        json_chain = []

        for block in self.chain:
            json_chain.append(block.to_json)
            
        return json_chain

    def valid_chain(self, chain):
        """
        Determine if a given blockchain is valid

        :param chain: A blockchain
        :return: True if valid, False if not
        """

        logging.info("Valid Chain Function")

        logging.debug("Received Chain")
        logging.debug(chain)

        # This will hold the Genesis Block.
        prev_block = chain[0]

        #TODO something's wrong in this function
        for cur_block in chain[1:]:
            block_reward_prev = None
            for transaction in prev_block['transactions']:
                if transaction['sender'] == '0':
                    block_reward_prev = transaction
                    break
            if block_reward_prev:
                prev_block['transactions'].remove(block_reward_prev)

            block_reward_cur = None
            for transaction in cur_block['transactions']:
                if transaction['sender'] == '0':
                    block_reward_cur = transaction
                    break
            if block_reward_cur:
                cur_block['transactions'].remove(block_reward_cur)

            # Check that the hash is correct.
            prev_block_hash = block_from_json(prev_block).hash

            if cur_block['previous_hash'] != prev_block_hash:
                logging.error("Bad Chain, Recieved hash: {} Expected hash: {}".format(cur_block['previous_hash'],prev_block_hash))
                logging.debug("Previous Block")
                logging.debug(block_from_json(prev_block).to_json)
                logging.debug("Prev Block #")
                logging.debug(prev_block['index'])
                logging.debug("Prev Block Proof")
                logging.debug(prev_block['proof'])
                logging.debug("Current Block")
                logging.debug(block_from_json(cur_block).to_json)
                logging.debug("Cur Block #:")
                logging.debug(cur_block['index'])
                logging.debug("Cur Block proof")
                logging.debug(cur_block['proof'])
                return False

            # Check that the proof of work is correct.
            if not self.valid_proof(prev_block['proof'], cur_block['proof'], prev_block_hash, cur_block['transactions']):
                logging.error("Bad Chain, Proof of work failed")
                return False

            if block_reward_cur:
                cur_block['transactions'].append(block_reward_cur)
            if block_reward_prev:
                prev_block['transactions'].append(block_reward_prev)
            prev_block = cur_block

        
        logging.info("Good Chain")
        return True

    def new_block(self, proof, previous_hash):
        """
        Create a new Block in the Blockchain

        :param proof: The proof given by the Proof of Work algorithm
        :param previous_hash: Hash of previous Block
        :return: New Block
        """
        block = Block(len(self.chain)+1,self.current_transactions,proof,previous_hash or self.chain[-1].hash,datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'))

        # Reset the current list of transactions
        self.current_transactions = []

        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount,timestamp):
        """
        Creates a new transaction to go into the next mined Block

        :param sender: Address of the Sender
        :param recipient: Address of the Recipient
        :param amount: Amount
        :return: The index of the Block that will hold this transaction
        """

        try:
            timestamp = timestamp.strftime('%Y-%m-%dT%H:%M:%SZ')
        except:
            pass
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
            'timestamp': timestamp
        })

        return self.last_block.index + 1

    @property
    def last_block(self):
        return self.chain[-1]

    def get_block(self, index):
        try:
            return self.chain[index]
        except:
            return -1

    def proof_of_work(self, last_block):
        """
        Simple Proof of Work Algorithm:

         - Find a number p' such that hash(pp') contains leading 4 zeroes
         - Where p is the previous proof, and p' is the new proof
         
        :param last_block: <Block> last Block
        :return: <int>
        """
        last_proof = last_block.proof
        last_hash = last_block.hash

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
        difficulty = config.get_block_difficulty()
        return guess_hash[:difficulty] == '0' * difficulty