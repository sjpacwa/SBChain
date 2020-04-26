"""
mine.py

This file is responsible for the miner functionality
"""

# Standard library imports
import logging
from datetime import datetime
from threading import Thread
import json

# Local imports
from macros import RECEIVE_BLOCK
from multicast import MulticastHandler


class Miner(Thread):
    """
    Miner
    """

    def __init__(self, metadata, queues):
        """
        __init__
    
        The constructor for a Miner object.

        :param node: <node Object> Node to do mining on
        """

        Thread.__init__(self)
        self.metadata = metadata
        self.queues = queues
        self.daemon = True
        self.start()

    def run(self):
        while True:
            mine(self.metadata, self.queues)


def proof_of_work(metadata, last_block):
    """
    proof_of_work()

    Not Thread Safe

    Proof of work algorithm

    TODO: consider including reward with the proof -> percentage of the transaction amount or other schema

    :return: <int> proof
    """

    current_trans = metadata['blockchain'].current_transactions

    last_proof = last_block.proof
    last_hash = last_block.hash

    logging.debug("Last Block Hash in mine function")
    logging.debug(last_block.hash)
    logging.debug("Last Block")
    logging.debug(last_block.to_json)

    proof = 0
    while not metadata['blockchain'].valid_proof(last_proof, proof, last_hash, current_trans):
        proof += 1

    return proof


def mine(*args, **kwargs):
    """
    mine()

    Not Thread Safe

    Mine a new Block

    """

    metadata = args[0]

    last_block = metadata['blockchain'].last_block
    
    # Remove reward from last block.
    block_reward = None
    for transaction in last_block.transactions:
        if transaction['sender'] == '0':
            block_reward = transaction
            break
    if block_reward:
        last_block.transactions.remove(block_reward)
    
    # Create the proof_of_work on the block.
    proof = proof_of_work(metadata, last_block)

    # Add reward back to last block.
    if block_reward:
        last_block.transactions.append(block_reward)

    # A reward is provided for a successful proof. This is marked as a 
    # newly minted coin by setting the sender to '0'.
    metadata['blockchain'].new_transaction(
        sender='0',
        recipient=metadata['uuid'],
        amount=1,
        timestamp=datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
    )

    # Create the new block and add it to the end of the chain.
    block = metadata['blockchain'].new_block(proof, last_block.hash)

    logging.debug("Mine peers:")
    logging.debug(metadata['peers'])
    MulticastHandler(metadata['peers']).multicast_wout_response(RECEIVE_BLOCK(block.to_json))

    logging.debug("Response:")
    logging.debug(block.to_json)

    logging.debug("My Chain")
    logging.debug(metadata['blockchain'].get_chain())

