"""
mine.py

This file is responsible for the miner functionality
"""

# Standard library imports
import logging
from datetime import datetime
from threading import Thread
from uuid import uuid4
import json

# Local imports
from coin import Coin, RewardCoin
from transaction import Transaction, RewardTransaction
from macros import RECEIVE_BLOCK
from connection import MultipleConnectionHandler


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


def proof_of_work(metadata, queues, reward, last_block):
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
        if not queues['trans'].empty():
            handle_transactions(metadata, queues, reward)
            
        proof += 1

    return proof


def handle_transactions(metadata, queues, reward_transaction):
    verified_transactions = []
    reward_coins = []
    while not queues['trans'].empty():
        transaction = queues['trans'].get()
        metadata['blockchain'].new_transaction(transaction)
        reward_coins.extend(transaction.get_all_reward_coins())

        verified_transactions.append(transaction)

    reward_coin = reward_transaction.get_all_output_coins()[0]
    reward_transaction.add_new_inputs(reward_coins)
    reward_coin.set_value(reward_transaction.get_values()[0])

    queues['tasks'].put(('forward_transaction', verified_transactions, {}, None))


def mine(*args, **kwargs):
    """
    mine()

    Not Thread Safe

    Mine a new Block

    """

    metadata = args[0]
    queues = args[1]

    blockchain = metadata['blockchain']

    last_block = blockchain.last_block

    # Create the reward transaction and add to working block.
    reward_id = str(uuid4()).replace('-', '')
    reward_transaction = RewardTransaction([], {metadata['uuid']: [RewardCoin(reward_id, 0)]}, reward_id)
    blockchain.update_reward(reward_transaction)

    # Create the proof_of_work on the block.
    proof = proof_of_work(metadata, queues, reward_transaction, last_block)

    # Create the new block and add it to the end of the chain.
    block = metadata['blockchain'].new_block(proof, last_block.hash)

    logging.debug("Mine peers:")
    logging.debug(metadata['peers'])
    MultipleConnectionHandler(metadata['peers']).send_wout_response(RECEIVE_BLOCK(block.to_json))

    logging.debug("Response:")
    logging.debug(block.to_json)

    logging.debug("My Chain")
    logging.debug(metadata['blockchain'].get_chain())

