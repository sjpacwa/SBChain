"""
mine.py

This file is responsible for the miner functionality

2020 Stephen Pacwa and Daniel Okazaki
Santa Clara University
"""

# Standard library imports
import logging
from copy import deepcopy
from random import randint
from sys import maxsize
from threading import Thread
from uuid import uuid4

# Local imports
from block import block_from_json
from blockchain import Blockchain
from coin import RewardCoin
from connection import MultipleConnectionHandler, SingleConnectionHandler
from history import History
from macros import RECEIVE_BLOCK, GET_CHAIN_PAGINATED, GET_CHAIN_PAGINATED_ACK, GET_CHAIN_PAGINATED_STOP, REWARD_COIN_VALUE
from transaction import RewardTransaction, transaction_verify


class BlockException(Exception):
    """
    BlockException

    This is a dummy exception that is used to notify that mining
    should be restarted.
    """

    pass


class Miner(Thread):
    """
    Miner
    """

    def __init__(self, metadata, queues):
        """
        __init__()

        The constructor for a Miner object.

        :param metadata: <dict> The metadata for this node.
        :param queues: <dict> The queues for this node.
        """

        Thread.__init__(self)
        self.metadata = metadata
        self.queues = queues
        self.daemon = True
        self.start()

    def run(self):
        """
        run()

        The run function that is used to start this threads functionality.
        """

        if self.metadata['benchmark']:
            logging.warning("Miner waiting at semaphore. Did you remember to call benchmark initialize?")
            self.metadata['benchmark_lock'].acquire()
            logging.warning("Semaphore acquired, proceeding to mine")

        while True:
            try:
                mine(self.metadata, self.queues)
            except BlockException:
                self.metadata['history'].get_lock().release()
                pass


def proof_of_work(metadata, queues, reward, last_block):
    """
    proof_of_work()

    Proof of work algorithm

    :param metadata: <dict> The metadata for this node.
    :param queues: <dict> The queues for this node.
    :param reward: <RewardTransaction Object> The reward
        transaction used in the new block.
    :param last_block: <Block Object> The previous block in the chain.

    :return: <int> The valid proof of work for this block.
    """

    current_trans = metadata['blockchain'].current_transactions

    last_proof = last_block.proof
    last_hash = last_block.hash

    history = History()
    history_lock = history.get_lock()

    proof = randint(0, maxsize)
    while not metadata['blockchain'].valid_proof(last_proof, proof, last_hash, current_trans):
        history_lock.acquire()

        if not queues['trans'].empty():
            handle_transactions(metadata, queues, reward)
        if not queues['blocks'].empty():
            handle_blocks(metadata, queues, reward)
        history_lock.release()

        if metadata['no_mine']:
            proof = proof
        else:
            if proof == maxsize:
                proof = 0
            else:
                proof += 1

    if not queues['blocks'].empty():
        handle_blocks(metadata, queues)

    history.add_transaction(current_trans[0])
    history.add_coin(current_trans[0].get_all_output_coins()[0])

    logging.debug("New proof: " + str(proof))

    return proof


def handle_transactions(metadata, queues, reward_transaction):
    """
    handle_transactions()

    This function handles new transactions that have been received
    off the network.

    :param metadata: <dict> The metadata for this node.
    :param queues: <dict> The queues for this node.
    :param reward_transaction: <RewardTransaction Object> The transaction
        used to track the reward value.
    """

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


def handle_blocks(metadata, queues, reward_transaction):
    """
    handle_blocks()

    This function handles new blocks that have been receieved off the
    network.

    :param metadata: <dict> The metadata for this node.
    :param queues: <dict> The queues for this node.
    :param reward_transaction: <RewardTransaction Object> The transaction
        used to track the reward value.

    :raise: <BlockException> When a block off the network is added to our
        chain.
    """

    history = History()

    changed = False
    while not queues['blocks'].empty():
        history_temp = history.get_copy()

        host_port, block = queues['blocks'].get()
        current_index = metadata['blockchain'].last_block_index

        if block.index == current_index + 1:
            success = verify_block(history_temp, block, metadata['blockchain'])
            if not success:
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
            if resolve_conflicts(block, history_temp, host_port, metadata, reward_transaction):
                changed = True

    if changed:
        queues['tasks'].put(('forward_block', [metadata['blockchain'].last_block, metadata['host'],
                                                metadata['port']], {}, None))
        queues['blocks'].task_done()
        raise BlockException


def resolve_conflicts(block, history_copy, host_port, metadata, reward_transaction):
    """
    resolve_conflicts

    This function handles resolving conflicts when the node receives a block
    that is much further ahead of us in index.

    :param block: <Block Object> The block that has been taken from the network.
    :param history_copy: <History Object> A copy of the history to allow us to edit it without issue.
    :param host_port: <tuple<str, int>> The host and port of the node that sent us the block.
    :param metadata: <dict> The metadata of the node.

    :return: <boolean> Whether or not the chain was replaced.
    """

    logging.debug("Resolving conflicts")

    blockchain_copy = deepcopy(metadata['blockchain'])

    try:
        conn = SingleConnectionHandler(host_port[0], host_port[1], False)
    except ConnectionRefusedError:
        return False

    response = conn.send_with_response(GET_CHAIN_PAGINATED(10))

    blocks = response['section']

    # Retrieve only the blocks that we need.
    while response['status'] != 'FINISHED':
        our_block = blockchain_copy.get_block(blocks[0]['index'])

        if our_block is not None and our_block.previous_hash == blocks[0]['previous_hash']:
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

        if our_block is None:
            continue

        if block['previous_hash'] == our_block.previous_hash:
            logging.debug("Found common ancestor")
            common_ancestor_index = our_block.index - 1
            break

    blocks = blocks[index + 1:]

    # Rollback current_transactions except the reward transaction
    cur_transactions = []
    if len(blockchain_copy.current_transactions) > 1:
        for transaction in blockchain_copy.current_transactions[1:]:
            cur_transactions.append(transaction)
            rollback_transaction(transaction, history_copy)
    # Rollback reward transactions
    reward_transaction.reset()

    # Rollback to common ancestor.
    for block in blockchain_copy.chain[-1:common_ancestor_index:-1]:
        rollback_block(block, history_copy)
        blockchain_copy.chain = blockchain_copy.chain[:-1]

    # Add new blocks moving forward.
    i = 0
    for block in blocks:
        block_obj = block_from_json(block)
        if block_obj is None:
            continue
        success = verify_block(history_copy, block_obj, blockchain_copy)
        blockchain_copy.add_block(block_obj)

        if not success:
            logging.debug("Could not replace chain")
            return False

        i = i + 1

    reward_coins = []
    # Roll forward current transactions
    if len(cur_transactions) > 0:
        for transaction in cur_transactions:
            if transaction_verify(history_copy, transaction):
                blockchain_copy.new_transaction(transaction)
                reward_coins.extend(transaction.get_all_reward_coins())

        reward_coin = reward_transaction.get_all_output_coins()[0]
        reward_transaction.add_new_inputs(reward_coins)
        reward_coin.set_value(reward_transaction.get_values()[0])

    blockchain_copy.increment_version_number()

    metadata['blockchain'].chain = blockchain_copy.chain
    metadata['blockchain'].current_transactions = blockchain_copy.current_transactions
    metadata['blockchain'].increment_version_number()

    metadata['history'].replace_history(history_copy)

    logging.info("Replaced chain with a longer one.")

    return True


def rollback_block(block, history_copy):
    """
    rollback_block

    This function rolls back a block in preparation for resolve conflicts.

    :param block: <Block Object> The block to rollback.
    :param history_copy: <History Object> The history object that can be changed.
    """

    reward_transaction = block.transactions[0]
    rollback_transaction(reward_transaction, history_copy)

    # Normal transactions.
    for transaction in block.transactions[-1:0:-1]:
        rollback_transaction(transaction, history_copy)


def rollback_transaction(transaction, history_copy):
    """
    rollback_transaction

    This function rolls back a transaction in preparation for resolve
    conflicts.

    :param transaction: <Transaction Object> The transaction to rollback.
    :param history_copy: <History Object> The history object that can be
        changed
    """

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

    This function starts the process of mining a new block.

    :param *args: Thread handler extra args.
    :param **kwargs: Thread handler extra args.
    """

    metadata = args[0]
    queues = args[1]

    blockchain = metadata['blockchain']

    last_block = blockchain.last_block

    # Create the reward transaction and add to working block.
    reward_id = str(uuid4()).replace('-', '')
    reward_transaction = RewardTransaction([], {metadata['uuid']: [RewardCoin(reward_id, REWARD_COIN_VALUE)]}, reward_id)
    blockchain.update_reward(reward_transaction)

    # Create the proof_of_work on the block.
    proof = proof_of_work(metadata, queues, reward_transaction, last_block)

    history = History()
    history.add_transaction(reward_transaction)

    # Create the new block and add it to the end of the chain.
    block = metadata['blockchain'].new_block(proof, last_block.hash)

    MultipleConnectionHandler(metadata['peers']).send_wout_response(RECEIVE_BLOCK(block.to_json(),
                                                                                    metadata['host'], metadata['port']))

    logging.debug("Mined block: " + block.to_string())


def verify_block(history_temp, block, blockchain):
    """
    verify_block()

    This function is responsible for verifying if a newly mined block
    can be added to our chain.

    :param history_temp: <History Object> A temporary history object for testing.
    :param block: <Block Object> The block object to add.
    :param blockchain: <Blockchain Object> The blockchain to add the block to. This
        is needed bacause sometimes we want to add to a copy of the blockchain.

    :return: <boolean> Whether the block was added or not.
    """

    new_transactions = []

    for transaction in block.transactions[1:]:
        hist_trans = history_temp.get_transaction(transaction.get_uuid())
        if hist_trans is not None:
            new_trans = transaction.to_string()
            hist_trans_string = hist_trans.to_string()

            if new_trans != hist_trans_string:
                # Transaction exists but does not match
                logging.debug('Bad block: transaction exists but does not match.')
                return False

            new_transactions.append(hist_trans)
        else:
            check = transaction_verify(history_temp, transaction)
            if not check:
                # Verification doesn't pass.
                logging.debug('Bad block: transaction verification fails')
                return False

            new_transactions.append(transaction)

    # Verify the reward.
    reward = block.transactions[0]
    hist_trans = history_temp.get_transaction(reward.get_uuid())
    if hist_trans is not None:
        new_trans = reward.to_string()
        hist_trans = hist_trans.to_string()

        # Transaction exists but does not match
        logging.debug('Bad block: reward already exists')
        return False
    else:
        check = transaction_verify(history_temp, reward, True)
        if not check:
            # Verification doesn't pass.
            logging.debug('Bad block: reward verification fails')
            return False

        new_transactions = [reward] + new_transactions

    lastblock = blockchain.last_block

    if lastblock.hash != block.previous_hash:
        logging.debug('Bad block: hash does not match')
        return False

    block.transactions = new_transactions

    if not Blockchain.valid_proof(lastblock.proof, block.proof, lastblock.hash, block.transactions):
        logging.debug('Bad block: invalid proof')
        return False

    return True
