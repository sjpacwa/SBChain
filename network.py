"""
network.py

This file is responsible for storing the class that is responsible for 
the socket-based main network loop.
"""

from math import ceil
from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread, Lock
import json
from datetime import datetime
import hashlib
import logging
#import sys

# Local Imports
from node import Node
from block import Block
from macros import *
from multicast import MulticastHandler

class NetworkHandler():
    def __init__(self, host, port, node, buffer_size=256):
        """
        __init__
        
        The constructor for a NetworkHandler object.

        :param host: (string) The IP address that the socket should be 
            bound to.
        :param port: (int) The port that the socket should be bound to.
        :param thread_functions: (dict) A dictionary that allows a 
            Thread to lookup a function object with a function name.
        :param buffer_size: (int) The size of the buffer used in data 
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

    def isActive(self):
        status = ""
        self.active_lock.acquire()
        status = self.active
        self.active_lock.release()
        return status
    def setActive(self,status):
        self.active_lock.acquire()
        self.active = status
        self.active_lock.release()

    def register_nodes(self,peers):
        """
        register_nodes

        Public.
        This function handles a POST request to /nodes/register. It 
        registers a peer with the node.
        """
        # Check that something was sent.
        logging.info("Registering Nodes")
        logging.debug(peers)
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
        logging.info(NODES(list(self.node.nodes)))

    def consensus(self):
        """
        consensus

        Public.
        This function handles a GET request to /nodes/resolve. It checks
        if the chain needs to be updated.
        """

        # TODO See what the standard is for this in bitcoin.

        replaced = self.node.resolve_conflicts()

        # Based on conflicts, generate a response of which chain is valid.
        if replaced:
            #logging.info("------------------------------------------------------------------------------------------------------------------------")
            logging.info("REPLACED")
            logging.info(REPLACED(self.node.blockchain.get_chain()))
            #logging.info("------------------------------------------------------------------------------------------------------------------------")

        else:
            #logging.info("------------------------------------------------------------------------------------------------------------------------")
            logging.info("Authoritative")
            logging.info(AUTHORITATIVE(self.node.blockchain.get_chain()))
            #logging.info("------------------------------------------------------------------------------------------------------------------------")


    def event_loop(self):
        """
        event_loop
        
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

            data_size, num_buffers = self._get_data_size(connection)
            connection.send(b'ACK')
            data = self._get_data(connection, data_size, num_buffers)

            self._dispatch_thread(connection, data)

    def _get_data_size(self, connection):
        """
        _get_data_size
        
        This function will listen on the connection for the size of the 
        future data.

        :param connection: (Socket) The new connection.
        :returns: (tuple) (data size, number of buffer cycles needed)
        """

        data_size = int(connection.recv(16).decode())
        logging.debug("Data size received:")
        logging.debug(data_size)
        
        logging.debug("Buffer Size Type {}".format(type(self.BUFFER_SIZE)))

        return (data_size, ceil(data_size / self.BUFFER_SIZE))

    def _get_data(self, connection, data_size, num_buffers):
        """
        _get_data
        This function will listen on the connection for the data.

        :param connection: The new connection.
        :param data_size: The size of the incoming data.
        :param num_buffers: The number of buffer cycles required.

        :return: JSON representation of the data.
        """

        data = ''
        for i in range(num_buffers):
            data += connection.recv(self.BUFFER_SIZE).decode()
        
        logging.debug("Data Receieved")
        logging.debug(data)

        return json.loads(data[:data_size])

    def _dispatch_thread(self, connection, data):
        """
        _dispatch_thread
        This function will dispatch a worker thread to handle the 
        request.

        :param connection: The new connection.
        :param data: JSON representation of the data.
        """

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
            logging.error('Dispatcher error: {}'.format(e))
            logging.error(data)

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

    def receive_block(self, connection,arguments):
        """
        receive_block

        Internal.
        This function handles a POST request to /block/receive_block. It 
        receives a block from a peer and forwards it along to everyone but 
        the original sender.
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
                


    def new_transaction(self, connection, arguments):
        """
        new_transaction

        Public.
        This function handles a POST request to /transactions/new. It 
        creates a new transaction and adds it to the pool of transactions.
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

        logging.debug(TRANSACTION_ADDED(block_index))


    def receive_transactions(self,connection,arguments):
        """
        receive_transaction

        Internal.
        This function handles a POST request to /transactions/receive_transaction. 
        It receives a transaction from a peer and forwards it along to everyone 
        but the original sender.
        """
        logging.info("Received transaction (from dispatcher)")

        # Create a new transaction.
        transaction = TRANSACTION(arguments['sender'],arguments['recipient'],arguments['amount'],arguments['timestamp'])
        # Compute the hash of the transaction for comparison.
        transaction_hash = hashlib.sha256(json.dumps(transaction, indent=4, sort_keys=True, default=str).encode())
        
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


    def full_chain(self,connection):
        logging.info("Received full_chain request (from dispatcher)")
        """
        full_chain

        Public.
        This function handles a GET request to /chain. It returns a copy of 
        the entire chain.
        """

        # TODO This needs to reply to the socket that is passed, it does not communicate to any other nodes, just returns local chain on socket.

        # Assemble the chain for the response.
        chain = CHAIN(self.node.blockchain.get_chain(),len(self.node.blockchain.get_chain()))
        chain = json.dumps(chain, indent=4, sort_keys=True, default=str).encode()
        logging.info(chain)
        data_len = len(chain)
        connection.send(str(data_len).encode())
        test = connection.recv(16).decode()
        logging.debug(test)        
        connection.send(chain)

    def get_block(self,connection,arguments):
        
        logging.info("Received get block request (from dispatcher)")

        """
        get_block

        Public.
        This function handles a GET request to /block/get_block. It returns 
        the block that has been requested.
        """

        # TODO Just need to respond to the connection.
        block = self.node.blockchain.get_block(arguments['values'].get('index'))

        block = json.dumps(block, indent=4, sort_keys=True, default=str).encode()
        logging.info(block)

        data_len = len(block)
        connection.send(str(data_len).encode())
        test = connection.recv(16).decode()
        logging.debug(test)        
        connection.send(block)
    
    def open_log(self,connection,arguments):
        host = arguments['host']
        port = arguments['port']

        logger = logging.getLogger()
        self.sh = logging.handlers.SocketHandler(host,port) # handler to write to socket
        logger.addHandler(self.sh)
        self.open_log = True

    def close_log(self,connection):
        node_id = self.node.identifier
        logger = logging.getLogger()

        if not open_log:
            logging.info("Log is not open over socket, please open the log")
            return

        logger.removeHandler(self.sh)
        self.sh.close()
        self.sh = None
        
        logs_path = "logs/" + node_id +".log"
   
    THREAD_FUNCTIONS = {
        "receive_block": receive_block,
        "new_transaction": new_transaction,
        "receieve_transactions": receive_transactions,
        "full_chain": full_chain,
        "get_block": get_block,
        "open_log": open_log,
        "close_log": close_log
    }