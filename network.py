"""
network.py

This file is responsible for storing the class that is responsible for 
the socket-based main network loop.
"""
# Standard library imports
from math import ceil
from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread, Lock
import json
from datetime import datetime
import hashlib
import logging

# Local Imports
from node import Node
from block import Block
from macros import *
from multicast import MulticastHandler
from mine import Miner

class NetworkHandler():
    """
    Single Connection Handler
    """
    def __init__(self, host, port, node, test, log_host = None, log_port = None, buffer_size=256):
        """
        __init__
        
        The constructor for a NetworkHandler object.

        :param host: <string> The IP address that the socket should be 
            bound to.
        :param port: <int> The port that the socket should be bound to.
        :param node: <Node Object> Node Object to interface with
        :param test: <bool> Testing mode(disable auto mine) if True else Normal Operation
        :param log_host: <string> The IP address of the logging interface server to connect to (optional)
        :param log_port: <bool> The port of the logging interface server to connect to (optional)
        :param buffer_size: <int> The size of the buffer used in data 
            transmission.
        """
        self.host = host
        self.port = port

        self.sock = None

        # TODO Update the thread functions to be supported as original.
        self.T_FUNCTIONS = self.THREAD_FUNCTIONS
        self.BUFFER_SIZE = int(buffer_size)

        self.node = node

        # TODO stop all threads waiting on things, need to send SIGKILL or something.
        self.active_lock = Lock()
        self.active = True

        self.sh = None
        self.open_log = False

        if log_host and log_port:
            logger = logging.getLogger()
            # handler to write to socket
            self.sh = logging.handlers.SocketHandler(log_host,log_port) 
            logger.addHandler(self.sh)
            self.open_log = True
        if test:
            self.received_block = (Lock(), False, None)
            self.miner = Miner(node,self.received_block)
            
    def isActive(self):
        """
        isActive()

        TODO

        Return the status of the network handler

        :return: <bool> True if network handler is active, else False
        """
        status = ""
        self.active_lock.acquire()
        status = self.active
        self.active_lock.release()
        return status
    def setActive(self,status):
        """
        setActive()

        TODO

        Set the status of the network handler
        
        :param status: <bool> True of Network Handler is working else False
        """
        self.active_lock.acquire()
        self.active = status
        self.active_lock.release()

    def register_nodes(self,peers):
        """
        register_nodes()

        Public

        Not Thread Safe

        This function is a public interface to regsiter nodes outside of the network handler dispatch thread

        Bad Practice: For testing purposes only

        NOTE: Will be deprecated in later versions of the code

        :param peers: <list> List of tuples (ip,port) of all peers to communicate with
        """
        # Check that something was sent.
        logging.info("Registering Nodes")
        logging.info(peers)
        if peers is None:
            logging.error("Error: No nodes supplied")
            return

        # Register the nodes that have been received.
        for peer in peers:
            logging.debug("Peer")
            logging.debug(peer)
            if peer[0] != self.host or peer[1] != self.port:
                logging.debug("Registering Node")
                self.node.register_node(peer[0],peer[1])

        # Generate a response to report that the peer was registered.
        logging.info("Peers")
        logging.info(json.dumps(NODES(list(self.node.nodes))))

    def consensus(self):
        """
        consensus()

        Not Thread Safe

        This function handles consensus when conflicts in chains appear. 
        This function is automatically called in the mine function
        """

        # TODO See what the standard is for this in bitcoin.

        replaced = self.node.resolve_conflicts()

        # Based on conflicts, generate a response of which chain is valid.
        if replaced:
            logging.info("REPLACED")
            logging.info(REPLACED(self.node.blockchain.get_chain()))

        else:
            logging.info("Authoritative")
            logging.info(AUTHORITATIVE(self.node.blockchain.get_chain()))

    def event_loop(self):
        """
        event_loop

        Not Thread Safe
        
        This function will setup the socket and wait for incoming 
        connections.
        """

        logging.info("Setting up socket and binding to %s:%s", self.host, 
            self.port)
        self.sock = socket(AF_INET, SOCK_STREAM)
        self.sock.bind((self.host, self.port))

        # Block while waiting for connections.
        while self.isActive():
            logging.info('Waiting for new connections')
            self.sock.listen(1)
            connection, client = self.sock.accept()
            logging.info('Created connection to %s:%s', client[0], 
                client[1])
            try:
                data_size, num_buffers = self._get_data_size(connection)
                connection.send(b'ACK')
                data = self._get_data(connection, data_size, num_buffers)

                self._dispatch_thread(connection, data)
            except ValueError:
                logging.error("Receieved invalid data format. Check README for description")
                connection.close()

    def _get_data_size(self, connection):
        """
        _get_data_size()

        Not Thread Safe
        
        This function will listen on the connection for the size of the 
        future data.

        :param connection: <Socket Connection Object> The new connection.
        :returns: <tuple> (data size <int>, number of buffer cycles needed <int>)
        """

        data_size = int(connection.recv(16).decode())
        logging.debug("Data size received:")
        logging.debug(data_size)
        
        logging.debug("Buffer Size Type {}".format(type(self.BUFFER_SIZE)))

        return (data_size, ceil(data_size / self.BUFFER_SIZE))

    def _get_data(self, connection, data_size, num_buffers):
        """
        _get_data()

        Not Thread Safe

        This function will listen on the connection for the data.

        :param connection: <Socket Connection Object> The new connection.
        :param data_size: <int> The size of the incoming data.
        :param num_buffers: <int> The number of buffer cycles required.

        :return: <json> JSON representation of the data.
        """

        data = ''
        for i in range(num_buffers):
            data += connection.recv(self.BUFFER_SIZE).decode()
        
        logging.debug("Data Receieved")
        logging.debug(data)

        return json.loads(data[:data_size])

    def _dispatch_thread(self, connection, data):
        """
        _dispatch_thread()

        Not Thread Safe

        This function will dispatch a worker thread to handle the 
        request.

        :param connection: <Socket Connection Object> The new connection.
        :param data: <json> JSON representation of the request. 
            Contains the name of the function to call and arguments for that function
        """
        function_name = None
        function_args = None
        try:
            function_name = data['name']
            function_args = data['args']

            logging.info('Dispatching function %s', function_name)
            th = Thread(
                target=self.T_FUNCTIONS[function_name],
                 args=(self,connection,) if not function_args else (self,connection, function_args,)
            )
            th.start()
        except Exception as e:
            if not function_args:
                th = Thread(target=self.T_FUNCTIONS[function_name], args=(self,connection,))
                th.start()
            else:
                th = Thread(target=self.T_FUNCTIONS[function_name], args=(self,connection,function_args,))
                th.start()
        except:
            logging.error("ERROR IN DISPATCHER")
            logging.error(data)
            self.setActive(False)
    
    def register_new_peers(self,connection,arguments):
        """
        register_new_peers()

        Public

        Not Thread Safe

        This function handles a request from the dispatcher. It 
        registers a peer with the node during runtime.
        
        :param connection: <Socket Connection Object> The new connection.
        :param peers: <list> A list of tuples (ip,port) of all peers
        """
        peers = arguments['peers']
        logging.info("Registering peers from dispatcher")

        self.register_nodes(peers)
        connection.close()

    def receive_block(self, connection,arguments):
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
        logging.info("Received Block (from dispatcher) with Block Number: {}".format(arguments['index']))
        # Create a block from the sent data.
        new_block = Block(
            index=arguments['index'],
            transactions=arguments['transactions'],
            proof=arguments['proof'],
            previous_hash=arguments['previous_hash'],
            timestamp=arguments['timestamp']
        )
        logging.info(new_block.to_string)
        
        # Ensure that this block has not been added before.
        for block in self.node.blockchain.chain:
            if new_block == block:
                logging.debug("Duplicate Block")
                connection.close()
                return

        else:
            # The block has not been added before. The proof should be 
            # checked.
            last_proof = self.node.blockchain.last_block.proof
            last_hash = self.node.blockchain.last_block.hash

            # Remove the reward from the block. If it is kept in, the proof 
            # will not be the same.
            block_reward = None
            for transaction in arguments['transactions']:
                if transaction['sender'] == '0':
                    block_reward = transaction
                    break
            if block_reward:
                arguments['transactions'].remove(block_reward)
            #logging.info("Arguments transactions")

            if self.node.blockchain.valid_proof(last_proof, arguments['proof'], last_hash, 
                arguments['transactions']):
                # The proof is valid and the block can be added. The reward 
                # transaction should be returned.
                if block_reward:
                    arguments['transactions'].append(block_reward)

                # Clear the pool of the transactions that are present in 
                # the mined block.
                for i in range(len(self.node.blockchain.current_transactions)):
                    for item in arguments['transactions']:
                        if self.node.blockchain.current_transactions[i] == item:
                            self.node.blockchain.current_transactions.remove(
                                self.node.blockchain.current_transactions[i])

                # Append the block to the chain.
                self.node.blockchain.chain.append(new_block)

                MulticastHandler(self.node.nodes).multicast_wout_response(RECEIVE_BLOCK(new_block.to_json))

                logging.info("-------------------")
                logging.info("Block Added")
                logging.info("-------------------")

            else:
                # The proof is not valid and the block is ignored and not 
                # propogated.
                logging.info("Bad Proof")
        connection.close()
                


    def new_transaction(self, connection, arguments):
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
        
        # NOTE: Currently, all transactions are considered valid. This 
        # means that 'fake' transactions will be added as well.
        
        logging.info("Creating new transaction (from dispatcher)")
        timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        transaction = TRANSACTION(arguments['sender'],arguments['recipient'],arguments['amount'],timestamp)

        # Create a new transaction from received data.
        block_index = self.node.blockchain.new_transaction(
            sender=arguments['sender'],
            recipient=arguments['recipient'],
            amount=arguments['amount'],
            timestamp=timestamp
        )

        MulticastHandler(self.node.nodes).multicast_wout_response(RECEIVE_TRANSACTION(transaction))

        logging.info(TRANSACTION_ADDED(block_index))
        connection.close()


    def receive_transactions(self,connection,arguments):
        """
        receive_transactions()

        Internal

        Not Thread Safe

        This function handles a request from the dispatcher (internal). 
        It receives a transaction from a peer and forwards it along to everyone 
        but the original sender.

        TODO: refactored in new branch to use coins


        :param connection: <Socket Connection Object> The new connection.
        :param sender: <str> Sender id for the transaction
        :param recipient: <str> Recipient id for the transaction
        :param amount: <int> Amount of the transaction 
        """
        logging.info("Received transaction (from dispatcher)")

        # Create a new transaction.
        transaction = TRANSACTION(arguments['sender'],arguments['recipient'],arguments['amount'],arguments['timestamp'])

        logging.info(transaction)
        # Compute the hash of the transaction for comparison.
        transaction_hash = hashlib.sha256(json.dumps(transaction, default=str).encode())
        
        # Make sure that the transaction doesn't match a previous one.
        # TODO need to implement a routing algorithm or verify transactions or we'll run into problems
        # I.E: Z nodes, node A creates transaction and adds to its block, forwards to all other blocks, Block Z gets transaction and forwards to Block A which is on a new blcok, Block A will add this transaction 
        # not realising that it was already added in another block
        for node_transaction in self.node.blockchain.current_transactions:
            node_transaction_hash = hashlib.sha256(node_transaction)
            if node_transaction_hash == transaction_hash:
                logging.info("Duplicate Transaction")

        else:
            #TODO add locks for thread safety? (for everything)
            # The transaction was not found. Add to the pool.
            self.node.blockchain.new_transaction(
                sender=arguments['sender'],
                recipient=arguments['recipient'],
                amount=arguments['amount'],
                timestamp=arguments['timestamp']
            )

            MulticastHandler(self.node.nodes).multicast_wout_response(RECEIVE_TRANSACTION(transaction))
            logging.info("Transaction added")
        connection.close()


    def full_chain(self,connection):
        """
        full_chain()

        Public and Internal

        This function handles a request from the dispatcher (public and internal).
        It returns a copy of the entire chain to the client.
        
        :param connection: <Socket Connection Object> The new connection.
        """

        logging.info("Received full_chain request (from dispatcher)")

        # Assemble the chain for the response.
        chain = CHAIN(self.node.blockchain.get_chain(),len(self.node.blockchain.get_chain()))
        logging.info(chain)
        chain = json.dumps(chain, default=str).encode()
        data_len = len(chain)
        connection.send(str(data_len).encode())
        test = connection.recv(16).decode()
        logging.debug(test)        
        connection.send(chain)
        connection.close()

    def get_block(self,connection,arguments):
        """
        get_block()

        Public and Internal

        This function handles a request from the dispatcher. 
        It returns the block that has been requested to the client.

        :param connection: <Socket Connection Object> The new connection.
        :param index: <int> Index of the block to send
        """
        
        logging.info("Received get block request (from dispatcher)")

        # TODO Just need to respond to the connection.
        block = self.node.blockchain.get_block(int(arguments))

        if isinstance(block,int):
            logging.error("Invalid block index")
            connection.close()
            return

        logging.info(block.to_string)

        block_to_string = block.to_string

        data_len = len(block_to_string)
        connection.send(str(data_len).encode())
        test = connection.recv(16).decode()
        logging.debug(test)        
        connection.send(block_to_string.encode())
        connection.close()
    
    def open_log(self,connection,arguments):
        """
        open_log()

        Public

        Not Thread Safe

        This function handles a request from the dispatcher. 
        It creates a socket connection to the logging server

        :param connection: <Socket Connection Object> The new connection.
        :param host: <str> Host IP of the logging server
        :param port: <int> Host port of the logging server
        """
        host = arguments['host']
        port = arguments['port']

        logger = logging.getLogger()
        self.sh = logging.handlers.SocketHandler(host,port) # handler to write to socket
        logger.addHandler(self.sh)
        self.open_log = True
        connection.close()

    def close_log(self,connection):
        """
        close_log()

        Public

        Not Thread Safe

        This function handles a request from the dispatcher. 
        It removes a socket connection to the logging server

        :param connection: <Socket Connection Object> The new connection.
        """
        node_id = self.node.identifier
        logger = logging.getLogger()

        if not open_log:
            logging.info("Log is not open over socket, please open the log")
            return

        logger.removeHandler(self.sh)
        self.sh.close()
        self.sh = None
        self.open_log = False
        connection.close()
    
    def mine(self,connection):
        """
        mine()

        Public

        Not Thread Safe

        This function handles a request from the dispatcher. 
        It processes a manual mine request

        NOTE: Only for testing purposes, do not use in normal operation

        :param connection: <Socket Connection Object> The new connection.
        """
        self.miner.mine()
        connection.close()
    
    # Functions that can be called by the dispatcher thread
    THREAD_FUNCTIONS = {
        "receive_block": receive_block,
        "new_transaction": new_transaction,
        "receieve_transactions": receive_transactions,
        "full_chain": full_chain,
        "get_block": get_block,
        "open_log": open_log,
        "close_log": close_log,
        "register_new_peers": register_new_peers,
        "mine": mine
    }