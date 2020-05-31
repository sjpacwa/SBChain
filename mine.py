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
from history import History


class BlockException(Exception):
    pass


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
            try:
                mine(self.metadata, self.queues)
            except BlockException:
                pass


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

    history = History()
    history_lock = history.get_lock()

    logging.debug("Last Block Hash in mine function")
    logging.debug(last_block.hash)
    logging.debug("Last Block")
    logging.debug(last_block.to_json())

    proof = 0
    while not metadata['blockchain'].valid_proof(last_proof, proof, last_hash, current_trans):
        history_lock.acquire()
        if not queues['trans'].empty():
            handle_transactions(metadata, queues, reward)
        if not queues['blocks'].empty():
            handle_blocks(metadata, queues)
        history_lock.release()
            
        proof += 1

    if not queues['blocks'].empty():
        handle_blocks(metadata, queues)

    history.add_transaction(current_trans[0])
    history.add_coin(current_trans[0].get_all_output_coins()[0])
    print(history.get_wallet().personal_coins)

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


def handle_blocks(metadata, queues):
    history = History()

    changed = False
    while not queues['blocks'].empty():
        history_temp = history.get_copy()

        host_port, block = queues['blocks'].get()
        current_index = metadata['blockchain'].last_block_index        
        if block.index == current_index:
            bad_block = False
            for transaction in block.transactions:
                hist_trans = history.get_transaction(transaction.get_uuid())
                if transaction_hist != None:
                    new_trans = transaction.to_string()
                    hist_trans = hist_trans.to_string()

                    if new_trans != hist_trans:
                        # Transaction exists but does not match
                        bad_block = True
                        break
                else:
                    check, _ = transaction_verify(history_temp, transaction)
                    if not check:
                        # Verification doesn't pass.
                        bad_block = True
                        break

            if bad_block:
                continue

            lastblock = metadata['blockchain'].last_block

            if lastblock.hash() != block.previous_hash:
                continue

        
            if not Blockchain.valid_proof(lastblock.proof, block.proof, lastblock.hash(), block.transactions):
                continue

            for transaction in block.transactions[1:]:
                try:
                    metadata['blockchain'].current_transactions.remove(transaction)
                except ValueError:
                    pass

            metadata['blockchain'].add_block(block)
            history.replace_history(history_temp)
            changed = True

        elif block.index > current_index:
            if resolve_conflicts(block, history_temp, host_port, metadata):
                changed = True

    if changed:
        queues['tasks'].put(('forward_block', metadata['blockchain'].last_block, {}, None))
        raise BlockException


def resolve_conflicts(block, history, host_port, metadata):
    print("resolve conflicts")
    print("Implement me!")
    return False


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
    reward_transaction = RewardTransaction([], {metadata['uuid']: [RewardCoin(reward_id, 5)]}, reward_id)
    blockchain.update_reward(reward_transaction)

    # Create the proof_of_work on the block.
    proof = proof_of_work(metadata, queues, reward_transaction, last_block)

    # Create the new block and add it to the end of the chain.
    block = metadata['blockchain'].new_block(proof, last_block.hash)

    logging.debug("Mine peers:")
    logging.debug(metadata['peers'])
    MultipleConnectionHandler(metadata['peers']).send_wout_response(RECEIVE_BLOCK(block.to_json()))

    logging.debug("Response:")
    logging.debug(block.to_json())

    logging.debug("My Chain")
    logging.debug(metadata['blockchain'].get_chain())

