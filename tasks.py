# Standard library imports
from urllib.parse import urlparse
import logging
from time import sleep

# Local imports
from coin import *
from transaction import *
from connection import MultipleConnectionHandler
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

    logging.info(block.to_string)

    block_to_string = block.to_string

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

    metadata = args[0]

    logging.info("Received Block (from dispatcher) with Block Number: {}".format(arguments['index']))
    # Create a block from the sent data.
    new_block = Block(
        index=block_data['index'],
        transactions=block_data['transactions'],
        proof=block_data['proof'],
        previous_hash=block_data['previous_hash'],
        timestamp=block_data['timestamp']
    )
    logging.info(new_block.to_string)
    
    # Ensure that this block has not been added before.
    for block in metadata['blockchain'].chain:
        if new_block == block:
            logging.debug("Duplicate Block")
            return

    else:
        # The block has not been added before. The proof should be 
        # checked.
        last_proof = metadata['blockchain'].last_block.proof
        last_hash = metadata['blockchain'].last_block.hash

        # Remove the reward from the block. If it is kept in, the proof 
        # will not be the same.
        block_reward = None
        for transaction in block_data['transactions']:
            if transaction['sender'] == '0':
                block_reward = transaction
                break
        if block_reward:
            block_data['transactions'].remove(block_reward)
        #logging.info("Arguments transactions")

        if metadata['blockchain'].valid_proof(last_proof, block_data['proof'], last_hash, 
            block_data['transactions']):
            # The proof is valid and the block can be added. The reward 
            # transaction should be returned.
            if block_reward:
                block_data['transactions'].append(block_reward)

            # Clear the pool of the transactions that are present in 
            # the mined block.
            for i in range(len(metadata['blockchain'].current_transactions)):
                for item in block_data['transactions']:
                    if metadata['blockchain'].current_transactions[i] == item:
                        metadata['blockchain'].current_transactions.remove(
                            metadata['blockchain'].current_transactions[i])

            # Append the block to the chain.
            metadata['blockchain'].chain.append(new_block)

            MultipleConnectionHandler(metadata['peers']).send_wout_response(RECEIVE_BLOCK(new_block.to_json))

            logging.info("-------------------")
            logging.info("Block Added")
            logging.info("-------------------")

        else:
            # The proof is not valid and the block is ignored and not 
            # propogated.
            logging.info("Bad Proof")


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

    history = metadata['history']
    history_lock = history.get_lock()

    with history_lock:
        for transaction in trans_data:
            # Check the transaction history.
            if history.get_transaction(transaction['uuid']) != None:
                # The transaction already exists.
                print("transaction exists")
                continue

            # Check input coins
            bad_transaction = False
            input_coins = []
            for coin in transaction['inputs']:
                found_coin = history.get_coin(coin['uuid'])
                if found_coin == None:
                    # The input coin does not exist.
                    print("input coin doesn't exist")
                    bad_transaction = True
                    break

                if found_coin.get_value() != coin['value'] or found_coin.get_transaction_id() != coin['transaction_id']:
                    # The coin does not match what we have in history.
                    print("input coin doesn't match")
                    bad_transaction = True
                    break

                input_coins.append(found_coin)

            if bad_transaction:
                continue

            # Check output coins
            output_coins = {}
            for recipient in transaction['outputs']:
                if bad_transaction:
                    break

                output_coins[recipient] = []

                for coin in transaction['outputs'][recipient]:
                    if history.get_coin(coin['uuid']):
                        logging.error('Fatal Error: This transaction contains an output coin that already exists: ' + str(transaction))
                        print("Output coin already exists")
                        bad_transaction = True
                        break
                    
                    output_coins[recipient].append(coin_from_json(coin))

            if bad_transaction:
                continue

            new_transaction = transaction_from_json(transaction, input_coins, output_coins)
            if new_transaction.verify():
                # The transaction looks proper. Remove inputs and add outputs to history.
                for coin in input_coins:
                    history.remove_coin(coin.get_uuid())

                for recipient in output_coins:
                    for coin in output_coins[recipient]:
                        history.add_coin(coin)

                # Add transaction to queue and history.
                queues['trans'].put(new_transaction)
                history.add_transaction(new_transaction)


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
def wait_test(sleep_time, message_id, *args, **kwargs):
    print("Start " + str(message_id))
    sleep(sleep_time)
    print("End " + str(message_id))

@thread_function
def response_test(*args, **kwargs):
    conn = args[2]

    message = '20~{"message": "hello"}'
    conn.send(message.encode())

