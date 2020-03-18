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
from macros import FULL_CHAIN

class Node:
    def __init__(self,node_id):
        self.nodes = []
        self.blockchain = Blockchain()
        self.identifier = node_id

    def resolve_conflicts(self):
        """
        This is our consensus algorithm, it resolves conflicts
        by replacing our chain with the longest one in the network.

        :return: True if our chain was replaced, False if not
        TODO: decide when to lock, what to do if resources are lcoked
        """

        neighbors = self.nodes
        our_chain = self.blockchain.chain
        replace_chain = None
        chain = None

        # We're only looking for chains longer than ours
        our_length = len(our_chain)

        responses = MulticastHandler(neighbors).multicast_with_response(FULL_CHAIN())
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
        Add a new node to the list of nodes

        :param address: Address of node. Eg. 'http://192.168.0.5:5000'

        NOTE: We assume that nodes don't drop later in the blockchain's lifespan
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
