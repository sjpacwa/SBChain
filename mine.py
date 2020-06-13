"""
mine.py

This file is responsible for the miner functionality
"""

# Standard library imports
import logging
from copy import deepcopy
from datetime import datetime
from threading import Thread
from uuid import uuid4
import json

# Local imports
from block import block_from_json   
from blockchain import Blockchain
from coin import Coin, RewardCoin
from transaction import Transaction, RewardTransaction, transaction_verify
from macros import RECEIVE_BLOCK, GET_CHAIN_PAGINATED, GET_CHAIN_PAGINATED_ACK, GET_CHAIN_PAGINATED_STOP
from connection import MultipleConnectionHandler, SingleConnectionHandler
from history import History
from encoder import ComplexEncoder


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
        if self.metadata['benchmark']:
            logging.warning("Miner waiting at semaphore. Did you remember to call benchmark initialize?")
            self.metadata['benchmark_lock'].acquire()
            logging.info("Semaphore acquired, proceeding to mine")

        while True:
            try:
                mine(self.metadata, self.queues)
            except BlockException:
                self.metadata['history'].get_lock().release()
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
           
        if metadata['debug']:
            proof = proof
        else:
            proof += 1

    if not queues['blocks'].empty():
        handle_blocks(metadata, queues)

    history.add_transaction(current_trans[0])
    history.add_coin(current_trans[0].get_all_output_coins()[0])

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

    queues['tasks'].put(('forward_transaction', [verified_transactions], {}, None))


def handle_blocks(metadata, queues):
    history = History()

    changed = False
    while not queues['blocks'].empty():
        logging.info("HERE")
        history_temp = history.get_copy()

        host_port, block = queues['blocks'].get()
        current_index = metadata['blockchain'].last_block_index        
        
        if block.index == current_index + 1:
            success = verify_block(history_temp, block, metadata['blockchain'])
            if success == False:
                queues['blocks'].task_done()
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
        queues['tasks'].put(('forward_block', [metadata['blockchain'].last_block, metadata['host'], metadata['port']], {}, None))
        queues['blocks'].task_done()
        raise BlockException


def resolve_conflicts(block, history_copy, host_port, metadata):
    logging.info("Resolving conflicts")

    blockchain_copy = deepcopy(metadata['blockchain'])

    logging.info(blockchain_copy)
    logging.info(blockchain_copy.chain)
    
    conn = SingleConnectionHandler(host_port[0], host_port[1], False)

    response = conn.send_with_response(GET_CHAIN_PAGINATED(10))

    blocks = response['section']

    # Retrieve only the blocks that we need.
    while response['status'] != 'FINISHED':
        our_block = blockchain_copy.get_block(blocks[0]['index'])

        if our_block != None and our_block.previous_hash == blocks[0]['previous_hash']:
            conn.send_wout_response(GET_CHAIN_PAGINATED_STOP())
            break

        response = conn.send_with_response(GET_CHAIN_PAGINATED_ACK())

        if response['status'] == 'INITIAL':
            blocks = response['section']
        else:
            blocks = response['section'] + blocks

    # Find common ancestor.
    common_ancestor_index = -1
    # logging.warning(blocks)
    for index, block in enumerate(blocks):
        net_index = block['index']
        our_block = blockchain_copy.get_block(net_index)

        if our_block == None:
            continue

        if block['previous_hash'] == our_block.previous_hash:
            logging.info("Found common ancestor")
            common_ancestor_index = our_block.index - 1
            break


    blocks = blocks[index + 1:]

    # Rollback to common ancestor.
    for block in blockchain_copy.chain[-1:common_ancestor_index:-1]:
        rollback_block(block, history_copy)
        blockchain_copy.chain = blockchain_copy.chain[:-1]

    # Add new blocks moving forward.
    i = 0
    for block in blocks:
        block_obj = block_from_json(block)
        success = verify_block(history_copy, block_obj, blockchain_copy)
        blockchain_copy.add_block(block_obj)
        if not success:
            logging.info("Could not replace chain")
            return False

        i = i + 1

    blockchain_copy.increment_version_number()

    metadata['blockchain'].chain = blockchain_copy.chain
    metadata['blockchain'].current_transactions = blockchain_copy.current_transactions
    metadata['blockchain'].increment_version_number()

    metadata['history'].replace_history(history_copy)

    logging.info("Replaced chain with a longer one.")

    return True


def rollback_block(block, history_copy):
    reward_transaction = block.transactions[0]
    rollback_transaction(reward_transaction, history_copy)

    # Normal transactions.
    for transaction in block.transactions[-1:0:-1]:
        rollback_transaction(transaction, history_copy)


def rollback_transaction(transaction, history_copy):
    output_coins = transaction.get_all_output_coins()
    for coin in output_coins:
        history_copy.remove_coin(coin.get_uuid())

    input_coins = transaction.get_inputs()
    for coin in input_coins:
        history_copy.add_coin(coin)

    history_copy.remove_transaction(transaction.get_uuid())


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

    history = History()
    history.add_transaction(reward_transaction)

    # Create the new block and add it to the end of the chain.
    block = metadata['blockchain'].new_block(proof, last_block.hash)

    logging.debug("Mine peers:")
    logging.debug(metadata['peers'])
    MultipleConnectionHandler(metadata['peers']).send_wout_response(RECEIVE_BLOCK(block.to_json(), metadata['host'], metadata['port']))

    logging.debug("Response:")
    logging.debug(block.to_json())

    logging.debug("My Chain")
    logging.debug(metadata['blockchain'].get_chain())


def verify_block(history_temp, block, blockchain):
    new_transactions = []

    for transaction in block.transactions[1:]:
        hist_trans = history_temp.get_transaction(transaction["uuid"])
        if hist_trans != None:
            new_trans = json.dumps(transaction)
            hist_trans_string = hist_trans.to_string()

            if new_trans != hist_trans_string:
                # Transaction exists but does not match
                logging.info('Bad block: transaction exists but does not match.')
                return False

            new_transactions.append(hist_trans)
        else:
            check, new_transaction = transaction_verify(history_temp, transaction)
            if not check:
                # Verification doesn't pass.
                logging.info('Bad block: transaction verification fails')
                return False

            new_transactions.append(new_transaction)

    # Verify the reward.
    reward = block.transactions[0]
    hist_trans = history_temp.get_transaction(reward.get_uuid())
    if hist_trans != None:
        new_trans = json.dumps(reward)
        hist_trans = hist_trans.to_string()

        # Transaction exists but does not match
        logging.warning('Bad block: reward already exists')
        return False

    else:
        check, new_reward = transaction_verify(history_temp, reward, True)
        if not check:
            # Verification doesn't pass.
            logging.info('Bad block: reward verification fails')
            return False

        new_transactions = [new_reward] + new_transactions

    lastblock = blockchain.last_block


    if lastblock.hash != block.previous_hash:
        logging.info('Bad block: hash does not match')
        return False

    block.transactions = new_transactions
    
    if not Blockchain.valid_proof(lastblock.proof, block.proof, lastblock.hash, block.transactions):
        logging.info('Bad block: invalid proof')
        return False

    return True
