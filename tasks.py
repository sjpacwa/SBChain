"""
tasks.py

This file holds all of the tasks that can be run.

2020 Stephen Pacwa and Daniel Okazaki
Santa Clara University
"""

# Standard library imports
from urllib.parse import urlparse
from hashlib import sha1
import logging
import json
from uuid import uuid4
from time import sleep
from datetime import datetime

# Local imports
from block import block_from_json
from coin import *
from transaction import *
from connection import MultipleConnectionHandler, ConnectionHandler, SingleConnectionHandler
from macros import RECEIVE_BLOCK, RECEIVE_TRANSACTION, REGISTER_NODES, SEND_CHAIN, SEND_CHAIN_SECTION, RESOLVE_CONFLICTS
from history import History


THREAD_FUNCTIONS = dict()


def thread_function(func):
    """
    register

    This function registers a function with the THREAD_FUNCTIONS
    dictionary.

    :param func: <Function Object> The function to be registered.
    """

    THREAD_FUNCTIONS[func.__name__] = func
    return func


"""
Public API calls.
"""


@thread_function
def get_chain(*args, **kwargs):
    """
    get_chain()

    This function returns a copy of the entire chain to the requestor.
    """

    metadata = args[0]
    conn = args[2]

    # Collect chain for response.
    chain = metadata['blockchain'].get_chain()
    length = len(chain)

    ConnectionHandler()._send(conn, SEND_CHAIN(chain, length))


@thread_function
def get_chain_paginated(size, *args, **kwargs):
    """
    get_chain_paginated()

    This function handles a request from the dispatcher (public and internal).
    It returns a subsection of the chain to the client and then waits for more messages.

    :param size: <integer> The number of blocks to receive
    """

    metadata = args[0]
    conn = args[2]

    if size < 1:
        ConnectionHandler()._send(conn, SEND_CHAIN_SECTION([], "ERROR"))

    while True:
        version_initial = metadata['blockchain'].get_version_number()
        chain = metadata['blockchain'].get_chain()
        offset = 0
        status = 'INITIAL'

        while True:
            version_inner = metadata['blockchain'].get_version_number()

            if version_inner != version_initial:
                break

            if offset == 0 and size < len(chain):
                section = chain[offset - size:]
                offset = offset - size
            elif offset == 0:
                section = chain
                status = 'FINISHED'
            elif abs(offset - size) > len(chain):
                section = chain[:offset]
                status = 'FINISHED'
            else:
                section = chain[offset - size:offset]
                offset = offset - size

            ConnectionHandler()._send(conn, SEND_CHAIN_SECTION(section, status))

            if status == 'INITIAL':
                status = 'CONTINUE'

            if status == 'FINISHED':
                return

            response = ConnectionHandler()._recv(conn)

            if response['params']['message'] == 'STOP':
                return


@thread_function
def get_block(index, *args, **kwargs):
    """
    get_block()

    This function handles a request from the dispatcher.
    It returns the block that has been requested to the client.

    :param connection: <Socket Connection Object> The new connection.
    :param index: <int> Index of the block to send
    """

    metadata = args[0]
    conn = args[2]

    logging.info("Received get block request (from dispatcher)")

    block = metadata['blockchain'].get_block(index)

    if block is None:
        ConnectionHandler()._send(conn, "Block does not exist")
        return

    ConnectionHandler()._send(conn, block)


@thread_function
def new_transaction(trans_data, *args, **kwargs):
    """
    new_transaction

    This function handles request from the dispatcher. It creates a new
    transaction and adds it to the list of transactions. Handles simpler transations than
    receive transaction.

    :param trans_data: <dict> The data of the transaction off the network.
    """

    metadata = args[0]
    queues = args[1]
    conn = args[2]

    history = History()
    wallet = history.get_wallet()
    wallet_lock = wallet.get_lock()

    trans_id = str(uuid4()).replace('-', '')

    input_value = trans_data['input']

    output_value = 0
    for recipient in trans_data['output']:
        output_value += trans_data['output'][recipient]

    reward = input_value - output_value

    with wallet_lock:
        coins_tuple, check = wallet.get_coins(trans_data['input'])

    if not check:
        ConnectionHandler()._send(conn, "Not enough coins")
        return

    coins, value = coins_tuple

    output_coins = {}
    # Normal output coins to other people.
    for recipient in trans_data['output']:
        coin = Coin(trans_id, trans_data['output'][recipient])

        if recipient in output_coins:
            output_coins[recipient].append(coin)
        else:
            output_coins[recipient] = [coin]

    # Reward coin.
    output_coins["SYSTEM"] = [Coin(trans_id, reward)]

    # Change.
    if value > 0:
        coin = Coin(trans_id, value)

        if metadata['uuid'] in output_coins:
            output_coins[metadata['uuid']].append(coin)
        else:
            output_coins[metadata['uuid']] = [coin]

    transaction = Transaction(metadata['uuid'], coins, output_coins, trans_id)
    transaction_json = transaction.to_json()

    response = receive_transaction_internal([transaction_json], metadata, queues)

    ConnectionHandler()._send(conn, response)


@thread_function
def register_nodes(peers, *args, **kwargs):
    """
    register_nodes()

    Add a new peer to the list of peers

    NOTE: We assume that nodes don't drop later in the blockchain's lifespan

    :param new_peers: <list> The address of the peer [[host, port], ...].

    :raises: <ValueError> When an invalid address is supplied.
    """

    metadata = args[0]

    if not isinstance(peers, list):
        return

    for peer in peers:
        logging.debug("Peer")
        logging.debug(peer)
        if isinstance(peer, list):
            peer = tuple(peer)
        else:
            continue

        if not len(peer) == 2:
            continue
        if not isinstance(peer[0], str):
            continue
        if not isinstance(peer[1], int):
            continue

        if peer[0] != metadata['host'] or peer[1] != metadata['port']:
            logging.debug("Registering Node")
            parsed_url = urlparse(peer[0])
            logging.debug("Parsed url")
            logging.debug(parsed_url)

            if parsed_url.netloc:
                new_peer = (parsed_url.netloc, peer[1])
                if new_peer not in metadata['peers']:
                    metadata['peers'].append(new_peer)
                    logging.debug(parsed_url.netloc, peer[1])
                else:
                    continue

            elif parsed_url.path:
                # Accepts an URL without scheme like '192.168.0.5:5000'.
                new_peer = (parsed_url.path, peer[1])
                if new_peer not in metadata['peers']:
                    metadata['peers'].append(new_peer)
                    logging.debug(str(parsed_url.path))
                    logging.debug(str(peer[1]))
                else:
                    continue

            else:
                logging.error('Invalid URL')
                logging.error(peer)
                continue

            # Connect to new node and give them our address. The outer list is
            # necessary because this function takes a list of nodes and the inner
            # list combines the host and port into one object.
            try:
                SingleConnectionHandler(
                    new_peer[0],
                    new_peer[1]
                ).send_wout_response(REGISTER_NODES([[metadata['host'], metadata['port']]]))
            except ConnectionRefusedError:
                pass


@thread_function
def unregister_nodes(peers, *args, **kwargs):
    """
    unregister_nodes()

    Remove peers from our list of peers.

    :param peers: <list> The address of the peers [[host, port], ...].
    """

    metadata = args[0]

    if not isinstance(peers, list):
        return

    for peer in peers:
        if isinstance(peer, list):
            peer = tuple(peer)
        else:
            continue

        try:
            metadata['peers'].remove(peer)
        except ValueError:
            pass
        logging.debug(peer)


@thread_function
def benchmark_initialize(node_ids, value, *args, **kwargs):
    """
    benchmark_initialize()

    This endpoint can be used in the case that the chain is being
    benchmarked to initialized each node in the system with a starting
    value. Note that for this to work properly, every node must
    successfully complete this task.

    :param node_ids: <list> A list of the node ids in the system.
    :param value: <int> The value to give each node.
    """

    metadata = args[0]

    # Only allow this to run once per node if benchmark is set to True.
    if not metadata['benchmark']:
        return False

    # Create the input coin.
    input_coin = Coin('BENCHMARK_ORIGIN', value * len(node_ids), 'BENCHMARK_INPUT')

    # Create the output coins.
    output_coins = {}
    for node_id in node_ids:
        sha1hash = sha1()
        sha1hash.update(node_id.encode())
        coin_id = sha1hash.digest().hex()

        coin = Coin('BENCHMARK_TRANS', value, coin_id)

        output_coins[node_id] = [coin]
        metadata['history'].add_coin(coin)

    # Create the transaction.
    transaction = Transaction(
        'BENCHMARK',
        [input_coin],
        output_coins,
        'BENCHMARK_TRANS',
        datetime.min.strftime('%Y-%m-%dT%H:%M:%SZ')
    )

    metadata['history'].add_transaction(transaction)

    # Add transaction to genesis block.
    metadata['blockchain'].chain[0].transactions.append(transaction)

    # Mark benchmark as false to prevent repeat calls and release the
    # semaphore so that mining can begin.
    metadata['benchmark'] = False
    metadata['benchmark_lock'].release()

    return True


@thread_function
def resolve_conflicts(*args, **kwargs):
    """
    resolve_conflicts()

    This function performs an active resolve conflicts, collecting
    information from all nodes in the network.
    """

    metadata = args[0]
    queues = args[1]
    conn = args[2]

    # Generate random ID for request.
    request_id = str(uuid4()).replace('-', '')
    metadata['resolve_requests'].add(request_id)

    # Send request to peers.
    host = metadata['host']
    port = metadata['port']
    length = metadata['blockchain'].last_block_index

    responses = MultipleConnectionHandler(metadata['peers']).send_with_response(RESOLVE_CONFLICTS(request_id, host, port, length))

    # Aggregate responses and wait for empty queue.
    blocks_sent = 0
    for response in responses:
        blocks_sent += response

    while not queues['blocks'].empty():
        pass

    # Notify caller process complete.
    ConnectionHandler()._send(conn, blocks_sent)


@thread_function
def get_balance(*args, **kwargs):
    """
    get_balance()

    This endpoint is used to get the wallet balance for this node
    """
    conn = args[2]

    history = History()
    wallet = history.get_wallet()
    wallet_lock = wallet.get_lock()

    with wallet_lock:
        balance = wallet.get_balance()

    ConnectionHandler()._send(conn, balance)


"""
Private API calls.
"""


@thread_function
def receive_block(block_data, host, port, *args, **kwargs):
    """
    receive_block()

    This function handles a request from the dispatcher (internal).
    It receives a block from a peer and forwards it along to everyone but
    the original sender.

    :param block_data: <dict> The data of the block off the network.
    :param host: <str> The host of the node that sent this request.
    :param port: <str> The port of the node that sent this request.
    """

    metadata = args[0]
    queues = args[1]

    current_index = metadata['blockchain'].last_block_index

    if block_data['index'] >= current_index + 1:
        block = block_from_json(block_data)
        if block is None:
            return

        logging.debug('Added block to queue')
        queues['blocks'].put(((host, port), block))


@thread_function
def receive_transactions(trans_data, *args, **kwargs):
    """
    receive_transaction()

    This function handles request from the dispatcher.
    It creates a new transaction and adds it to the pool of transactions.

    :param trans_data: <dict> The data of the transactions off the network.
    """

    metadata = args[0]
    queues = args[1]

    receive_transaction_internal(trans_data, metadata, queues)


def receive_transaction_internal(trans_data, metadata, queues):
    """
    receive_transaction_internal()

    This function is an internal version to allow new transactions on the node to
    be added without going through the network.

    :param trans_data: <dict> The data of the transactions off the network.
    """

    history = metadata['history']
    history_lock = history.get_lock()

    with history_lock:
        transactions = []
        for transaction in trans_data:
            new_transaction = transaction_from_json(transaction)
            check = transaction_verify(history, new_transaction)
            if check:
                queues['trans'].put(new_transaction)
                transactions.append(new_transaction.to_json())
            else:
                transactions.append('{"status": "Transaction verification failed", "transaction": ' + json.dumps(transaction) + '}')

    return transactions


@thread_function
def forward_transaction(transaction_list, *args, **kwargs):
    """
    forward_transaction()

    This function forwards a transaction to the peers of this node.

    :param transaction_list: <list<Transaction Object>> The transactions to
        forward to peers
    """

    metadata = args[0]

    connection = MultipleConnectionHandler(metadata['peers'])

    message = RECEIVE_TRANSACTION(transaction_list)

    connection.send_wout_response(message)


@thread_function
def forward_block(block, host, port, *args, **kwargs):
    """
    forward_block()

    This function forwards a block to the peers of this node.

    :param block: <Block Object> The block to forward to peers.
    :param host: <str> The host that is forwarding the block.
    :param port: <int> The port that is forwarding the block.
    """

    metadata = args[0]

    connection = MultipleConnectionHandler(metadata['peers'])

    message = RECEIVE_BLOCK(block, host, port)

    connection.send_wout_response(message)


@thread_function
def resolve_conflicts_internal(request_id, host, port, current_index, *args, **kwargs):
    """
    resolve_conflicts_internal

    The private analogue to resolve_conflicts. This propogates the message
    and sends their latest block to the node that made the original request.

    :param request_id: <str> The ID of this request.
    :param host: <str> The host of the original requestor.
    :param port: <int> The port of the original requestor.
    :param current_index: <int> The index of the original requestor.
    """

    metadata = args[0]
    conn = args[2]

    metadata['resolve_lock'].acquire()

    if request_id in metadata['resolve_requests']:
        ConnectionHandler()._send(conn, 0)
        return

    metadata['resolve_requests'].add(request_id)

    metadata['resolve_lock'].release()

    responses = MultipleConnectionHandler(metadata['peers']).send_with_response(RESOLVE_CONFLICTS(request_id, host, port, current_index))

    blocks_sent = 0
    for response in responses:
        blocks_sent += response

    if metadata['blockchain'].last_block_index > current_index:
        try:
            SingleConnectionHandler(host, port).send_wout_response(RECEIVE_BLOCK(metadata['blockchain'].last_block, metadata['host'], metadata['port']))
        except ConnectionRefusedError:
            ConnectionHandler()._send(conn, blocks_sent)
            return
        ConnectionHandler()._send(conn, blocks_sent + 1)


"""
Testing API calls.
"""


@thread_function
def wait_test(sleep_time, message_id, *args, **kwargs):
    """
    wait_test()

    This function performs a simple wait for testing.

    :param sleep_time: <int> The number of seconds to sleep.
    :param message_id: <str> The message to display.
    """

    logging.info("Inside wait test")
    sleep(sleep_time)


@thread_function
def response_test(*args, **kwargs):
    """
    response_test()

    This function performs a simple response for testing.
    """

    conn = args[2]

    message = '20~{"message": "hello"}'
    conn.send(message.encode())
