# Standard library imports
from urllib.parse import urlparse
import logging
from time import sleep

# Local imports
from mine import mine
from multicast import MulticastHandler


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

    
def mine(*args, **kwargs):
    """
    mine()

    Public

    Not Thread Safe

    This function handles a request from the dispatcher. 
    It processes a manual mine request

    NOTE: Only for testing purposes, do not use in normal operation

    :param connection: <Socket Connection Object> The new connection.
    """

    pass
    # self.miner.mine()
    # TODO need to rethink mining here.


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

            MulticastHandler(metadata['peers']).multicast_wout_response(RECEIVE_BLOCK(new_block.to_json))

            logging.info("-------------------")
            logging.info("Block Added")
            logging.info("-------------------")

        else:
            # The proof is not valid and the block is ignored and not 
            # propogated.
            logging.info("Bad Proof")


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
    
    # NOTE: Currently, all transactions are considered valid. This 
    # means that 'fake' transactions will be added as well.
    
    logging.info("Creating new transaction (from dispatcher)")
    timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
    transaction = TRANSACTION(trans_data['sender'],trans_data['recipient'],trans_data['amount'],timestamp)

    # Create a new transaction from received data.
    block_index = metadata['blockchain'].new_transaction(
        sender=trans_data['sender'],
        recipient=trans_data['recipient'],
        amount=trans_data['amount'],
        timestamp=timestamp
    )

    MulticastHandler(metadata['peers']).multicast_wout_response(RECEIVE_TRANSACTION(transaction))

    logging.info(TRANSACTION_ADDED(block_index))


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


def test(sleep_time, message_id, *args, **kwargs):
    print("Start " + str(message_id))
    sleep(sleep_time)
    print("End " + str(message_id))


# Functions that can be called by the dispatcher thread
THREAD_FUNCTIONS = {
    "full_chain": full_chain,
    "get_block": get_block,
    "mine": mine,
    "receive_block": receive_block,
    "receieve_transactions": receive_transactions,
    "register_nodes": register_nodes,
    "test": test,
}

