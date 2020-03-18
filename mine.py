# Standard Library Imports
import logging
from datetime import datetime
from threading import Thread
import json


#local imports
from macros import NEIGHBORS, RECEIVE_BLOCK
from network import NetworkHandler
from multicast import MulticastHandler

class Miner():
    network_handler = None
    node = None
    blockchain = None

    new_block = {}

    def __init__(self, network_handler, new_block):
        self.network_handler = network_handler
        self.node = self.network_handler.node
        self.blockchain = self.node.blockchain

        self.new_block = new_block

    def mine(self):
        last_block = self.blockchain.last_block
        
        # Remove reward from last block.
        block_reward = None
        for transaction in last_block.transactions:
            if transaction['sender'] == '0':
                block_reward = transaction
                break
        if block_reward:
            last_block.transactions.remove(block_reward)
        
        # Create the proof_of_work on the block.
        proof = self.proof_of_work(last_block)

        # Add reward back to last block.
        if block_reward:
            last_block.transactions.append(block_reward)

        # A reward is provided for a successful proof. This is marked as a 
        # newly minted coin by setting the sender to '0'.
        self.blockchain.new_transaction(
            sender='0',
            recipient=self.node.identifier,
            amount=1,
            timestamp=datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        )

        # Create the new block and add it to the end of the chain.
        block = self.blockchain.new_block(proof, last_block.hash)

        logging.debug("Mine peers:")
        logging.debug(self.node.nodes)
        MulticastHandler(self.node.nodes).multicast_wout_response(RECEIVE_BLOCK(block.to_json))
        self.network_handler.consensus()

        logging.debug("Response:")
        logging.debug(json.dumps(block.to_json, indent=4, sort_keys=True, default=str))

        logging.debug("My Chain")
        logging.debug(self.blockchain.get_chain())

    def proof_of_work(self, last_block):
        last_proof = last_block.proof
        last_hash = last_block.hash
        current_trans = self.blockchain.current_transactions

        logging.debug("Last Block Hash in mine function")
        logging.debug(last_block.hash)
        logging.debug("Last Block")
        logging.debug(last_block.to_json)

        proof = 0
        while not self.blockchain.valid_proof(last_proof, proof, last_hash, current_trans):
            proof += 1

            # Check if a new block was received from network.
            self.new_block[0].acquire()
            if self.new_block[1]:
                # A block has been received and not handled.
                # TODO Check index, proof, etc. and handle.
                # TODO This is where new blocks should be added if they are valid.
                # TODO If a block is valid to be added, do that and restart mining.
                
                # Mark that this block has been handled.
                self.new_block[1] = False

            self.new_block[0].release()

        return proof

    def check_new_block(self):
        pass

        

def mine(network_handler, node):
    """
    mine

    Public.
    This function handles a GET request to /mine. It creates a new 
    block with a valid proof and add it to the end of the blockchain. 
    This block is then propogated to the node's peers.
    TODO: Decide when to lock resources, what to do if resources are already locked
    """

    #TODO 
    # Get a valid proof of work for the last block in the chain.
    last_block = node.blockchain.last_block

    # Remove the reward from the block. If it is kept in, the proof 
    # will not be the same.
    block_reward = None
    for transaction in last_block.transactions:
        if transaction['sender'] == '0':
            block_reward = transaction
            break
    if block_reward:
        last_block.transactions.remove(block_reward)

    logging.debug("Last Block Hash in mine function")
    logging.debug(last_block.hash)
    logging.debug("Last Block")
    logging.debug(last_block.to_json)

    #TODO potential problem where receieving transactions during/after proof is set, undefined behavior?
    # I.E proof created with missing transactions
    #my_transactions = network_handler.node.blockchain.current_transactions
    proof = node.blockchain.proof_of_work(last_block, received_block)

    # A reward is provided for a successful proof. This is marked as a 
    # newly minted coin by setting the sender to '0'.
    node.blockchain.new_transaction(
        sender='0',
        recipient=node.identifier,
        amount=1,
        timestamp=datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
    )
    # Create the new block and add it to the end of the chain.
    block = node.blockchain.new_block(proof, last_block.hash)

    # add back reward
    if block_reward:
        last_block.transactions.append(block_reward)

    logging.debug("Mine peers:")
    logging.debug(network_handler.node.nodes)
    MulticastHandler(node.nodes).multicast_wout_response(RECEIVE_BLOCK(block.to_json))
    network_handler.consensus()

    logging.debug("Response:")
    logging.debug(json.dumps(block.to_json, indent=4, sort_keys=True, default=str))

    logging.debug("My Chain")
    logging.debug(node.blockchain.get_chain())
    logging.info("Mined a Block")



def mine_loop(network_handler, received_block):
    miner = Miner(network_handler, received_block)

    while network_handler.isActive():
        miner.mine()
