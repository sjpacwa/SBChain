"""
node.py
This file defines the Node class which is used to store information node 
specific information.
"""

# Standard library imports
import json
from urllib.parse import urlparse
from uuid import uuid4
import logging
from threading import Lock

# Local imports
from blockchain import Blockchain
from block import Block, block_from_json
from multicast import MulticastHandler
from macros import GET_CHAIN

class Node:
    """
    Node
    """
    def __init__(self,node_id):
        """
        __init__
        
        The constructor for a Single Connection Handler object

        :param node_id: <str> Identifier for the node.
        """
        self.nodes = []
        self.blockchain = Blockchain()
        self.identifier = node_id

    def resolve_conflicts(self):
        """
        reslove_conflicts()

        Not Thread Safe

        Consensus algorithm at the node level

        :returns: <bool> True if our chain was replaced, else False
        """

        neighbors = self.nodes
        our_chain = self.blockchain.chain
        replace_chain = None
        chain = None

        # We're only looking for chains longer than ours
        our_length = len(our_chain)

        responses = MulticastHandler(neighbors).multicast_with_response(GET_CHAIN())
        logging.debug("Responses")
        logging.debug(responses)

        # Grab and verify the chains from all the nodes in our network
        for response in responses:
            if "Error" not in response:
                neighbor_length = response['length']
                neighbor_chain = response['chain']

                # Check if the neighbors chain is longer and if it is valid.
                if (neighbor_length > our_length 
                    and self.blockchain.valid_chain(neighbor_chain)):
                    our_length = neighbor_length
                    chain = response['chain']
        if chain:
            logging.info("Replaced chain")
            logging.info(chain)
            # Replace our chain if we discovered a new, valid chain longer than ours
            replace_chain = []
            for block in chain:
                replace_chain.append(block_from_json(block))
            self.blockchain.chain = replace_chain
            return True
        return False

    def register_node(self, address,port):
        """
        register_nodes()

        Add a new peer to the list of nodes

        NOTE: We assume that nodes don't drop later in the blockchain's lifespan


        :param address: <str> Address of peer. Eg. 'http://192.168.0.5:5000'
        :param port: <int> Port of peer.

        :raises: <ValueError> If the address is invalid
        """

        logging.debug("Registering Node")
        parsed_url = urlparse(address)
        logging.debug("Parsed url")
        logging.debug(parsed_url)
        if parsed_url.netloc:
            self.nodes.append((parsed_url.netloc,port))
            logging.debug(parsed_url.netloc,port)
        elif parsed_url.path:
            # Accepts an URL without scheme like '192.168.0.5:5000'.
            self.nodes.append((parsed_url.path,port))
            logging.debug(parsed_url.path,port)
        else:
            logging.error('Invalid URL')
            raise ValueError('Invalid URL')
