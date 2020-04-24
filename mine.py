"""
mine.py

This file is responsible for the miner functionality
"""

# Standard Library Imports
import logging
from datetime import datetime
from threading import Thread
import json


#local imports
from macros import NEIGHBORS, RECEIVE_BLOCK
from multicast import MulticastHandler

class Miner():
    """
    Miner
    """
    node = None
    blockchain = None


    def __init__(self, blockchain, identifier, nodes):
        """
        __init__
    
        The constructor for a Miner object.

        :param node: <node Object> Node to do mining on
        """
        
        self.blockchain = blockchain
        self.identifier = identifier
        self.nodes = nodes

    def mine(self):
        """
        mine()

        Not Thread Safe

        Mine a new Block

        """
        last_block = self.blockchain.last_block
        
        # Remove reward from last block.
        block_reward = None
        for transaction in last_block.transactions:
            if transaction['sender'] == '0':
                block_reward = transaction
                break
        if block_reward:
            last_block.transactions.remove(block_reward)
        
        # Create the proof_of_work on the block.
        proof = self.proof_of_work(last_block)

        # Add reward back to last block.
        if block_reward:
            last_block.transactions.append(block_reward)

        # A reward is provided for a successful proof. This is marked as a 
        # newly minted coin by setting the sender to '0'.
        self.blockchain.new_transaction(
            sender='0',
            recipient=self.identifier,
            amount=1,
            timestamp=datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        )

        # Create the new block and add it to the end of the chain.
        block = self.blockchain.new_block(proof, last_block.hash)

        logging.debug("Mine peers:")
        logging.debug(self.nodes)
        MulticastHandler(self.nodes).multicast_wout_response(RECEIVE_BLOCK(block.to_json))

        logging.debug("Response:")
        logging.debug(block.to_json)

        logging.debug("My Chain")
        logging.debug(self.blockchain.get_chain())

    def proof_of_work(self, last_block):
        """
        proof_of_work()

        Not Thread Safe

        Proof of work algorithm

        TODO: consider including reward with the proof -> percentage of the transaction amount or other schema

        :return: <int> proof
        """
        last_proof = last_block.proof
        last_hash = last_block.hash
        current_trans = self.blockchain.current_transactions

        logging.debug("Last Block Hash in mine function")
        logging.debug(last_block.hash)
        logging.debug("Last Block")
        logging.debug(last_block.to_json)

        proof = 0
        while not self.blockchain.valid_proof(last_proof, proof, last_hash, current_trans):
            proof += 1

        return proof

    def check_new_block(self):
        """
        check_new_block()

        Not Thread Safe

        TODO: check block logic
        """
        pass


def mine_loop(blockchain, identifier, nodes):
    """
    mine_loop()

    While the network handler is active, mine a block

    """
    miner = Miner(blockchain, identifier, nodes)

    while 1:
        miner.mine()

