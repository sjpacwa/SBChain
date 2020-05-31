# Standard library imports
from urllib.parse import urlparse
import logging
import json
from time import sleep

# Local imports
from block import Block
from coin import *
from encoder import ComplexEncoder
from transaction import *
from connection import MultipleConnectionHandler, ConnectionHandler
from mine import mine


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


@thread_function
def full_chain(*args, **kwargs):
    """
    full_chain()

    Public and Internal

    This function handles a request from the dispatcher (public and internal).
    It returns a copy of the entire chain to the client.
    
    :param connection: <Socket Connection Object> The new connection.
    """

    metadata = args[0]
    connection = args[2]

    logging.info("Received full_chain request (from dispatcher)")

    # Assemble the chain for the response.
    chain = CHAIN(metadata['blockchain'].get_chain(),len(metadata['blockchain'].get_chain()))
    logging.info(chain)
    chain = json.dumps(chain, default=str).encode()
    data_len = len(chain)
    connection.send(str(data_len).encode())
    test = connection.recv(16).decode()
    logging.debug(test)        
    connection.send(chain)


@thread_function
def get_block(arguments, *args, **kwargs):
    """
    get_block()

    Public and Internal

    This function handles a request from the dispatcher. 
    It returns the block that has been requested to the client.

    :param connection: <Socket Connection Object> The new connection.
    :param index: <int> Index of the block to send
    """

    metadata = args[0]
    connection = args[2]
    
    logging.info("Received get block request (from dispatcher)")

    # TODO Just need to respond to the connection.
    block = metadata['blockchain'].get_block(int(arguments))

    if isinstance(block,int):
        logging.error("Invalid block index")
        return

    logging.info(block.to_string())

    block_to_string = block.to_string()

    data_len = len(block_to_string)
    connection.send(str(data_len).encode())
    test = connection.recv(16).decode()
    logging.debug(test)        
    connection.send(block_to_string.encode())


@thread_function
def receive_block(block_data, *args, **kwargs):
    """
    receive_block()

    Internal

    Not Thread Safe

    This function handles a request from the dispatcher (internal).
    It receives a block from a peer and forwards it along to everyone but 
    the original sender.

    :param connection: <Socket Connection Object> The new connection.
    :param index: <int> Index of the block
    :param transactions: <json> JSON representation of transactions.
    :param proof: <int> Proof of block
    :param previous hash: <str> Hash of the previous block
    :param timestamp: <timestamp> Timestamp of the block creation
    """

    print("START")
    print(block_data)
    print(args)
    print("END")

    metadata = args[0]
    queues = args[1]
    conn = args[2]

    
    host, port = conn.getpeername()

    current_index = metadata['blockchain'].last_block_index

    print(block_data)

    if block_data['index'] >= current_index:
        transactions = []

        """
        try:
            reward = block_data['transactions'][0]
            inputs = json.loads(reward['inputs'], cls=ComplexEncoder)
            outputs = {}
            for i in outputs:
                outputs[i] = RewardCoin(outputs[i][0]['transaction_id'], outputs[i][0]['value'], outputs[i][0]['uuid'])

            transactions.append(transaction_from_json(reward, inputs, outputs))
        except IndexError:
            pass

        for transaction in block_data['transactions'][1:]:
            inputs = json.loads(transaction['inputs'], cls=ComplexEncoder)
            outputs = json.loads(transaction['outputs'], cls=ComplexEncoder)
            transactions.append(transaction_from_json(transaction, inputs, outputs))
        """
        block = Block(
            index=block_data['index'],
            transactions=block_data['transactions'],
            proof=block_data['proof'],
            previous_hash=block_data['previous_hash'],
            timestamp=block_data['timestamp']
        )

        queues['blocks'].put(((host, port), block))


@thread_function
def receive_transactions(trans_data, *args, **kwargs):
    """
    new_transaction()

    Public

    Not Thread Safe

    This function handles request from the dispatcher (public). 
    It creates a new transaction and adds it to the pool of transactions.

    TODO: refactored in new branch to use coins
    
    :param connection: <Socket Connection Object> The new connection.
    :param sender: <str> Sender id for the transaction
    :param recipient: <str> Recipient id for the transaction
    :param amount: <int> Amount of the transaction 
    """

    metadata = args[0]
    queues = args[1]

    receive_transaction_internal(trans_data, metadata, queues)
                

def receive_transaction_internal(trans_data, metadata, queues):
    history = metadata['history']
    history_lock = history.get_lock()

    transactions = []

    with history_lock:
        for transaction in trans_data:
            check, new_transaction = transaction_verify(history, transaction)
            if check:
                queues['trans'].put(new_transaction)
                transactions.append(new_transaction.to_json())
            else:
                transactions.append('Transaction verfication failed' + str(transaction))

    return transactions


@thread_function
def new_transaction(trans_data, *args, **kwargs):

    print("HERE")

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
    print(value)
    print(input_value)
    if value > 0:
        coin = Coin(trans_id, value)

        if metadata['uuid'] in output_coins:
            output_coins[metadata['uuid']].append(coin)
        else:
            output_coins[metadata['uuid']] = [coin]

    transaction = Transaction(metadata['uuid'], coins, output_coins, trans_id)
    transaction_json = [transaction.to_json()]

    print("check 1")
    print(transaction_json)

    response = receive_transaction_internal(transaction_json, metadata, queues)

    ConnectionHandler()._send(conn, response)


@thread_function
def register_nodes(new_peers, *args, **kwargs):
    """
    register_nodes()

    Add a new peer to the list of peers

    NOTE: We assume that nodes don't drop later in the blockchain's lifespan

    :param new_peers: <list> The address of the peer [host, port].
    :param *args: <tuple> (metadata, queues, conn).
    :param **kwargs: <dict> Additional arguments.

    :raises: <ValueError> When an invalid address is supplied.
    """

    metadata = args[0]

    for peer in new_peers:
        logging.debug("Peer")
        logging.debug(peer)

        if peer[0] != metadata['host'] or peer[1] != metadata['port']:
            logging.debug("Registering Node")
            parsed_url = urlparse(peer[0])
            logging.debug("Parsed url")
            logging.debug(parsed_url)
            
            if parsed_url.netloc:
                metadata['peers'].append((parsed_url.netloc,peer[1]))
                logging.debug(parsed_url.netloc,peer[1])
            
            elif parsed_url.path:
                # Accepts an URL without scheme like '192.168.0.5:5000'.
                metadata['peers'].append((parsed_url.path,peer[1]))
                logging.debug(parsed_url.path,peer[1])
            
            else:
                logging.error('Invalid URL')
                logging.error(peer)


@thread_function
def forward_transaction(transaction_list, *args, **kwargs):
    metadata = args[0]

    connection = MultipleConnectionHandler(metadata['peers'])

    message = {
            "action": "receive_transaction",
            "params": transaction_list,
        }

    connection.send_wout_response(json.dumps(message, cls=ComplexEncoder))


@thread_function
def wait_test(sleep_time, message_id, *args, **kwargs):
    print("Start " + str(message_id))
    sleep(sleep_time)
    print("End " + str(message_id))

@thread_function
def response_test(*args, **kwargs):
    conn = args[2]

    message = '20~{"message": "hello"}'
    conn.send(message.encode())

