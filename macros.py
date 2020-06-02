"""
blockchain.py

This file defines the Blockchain class which is used to manage information 
related to the chain.
"""

TEST_MODE = False

BUFFER_SIZE = 256

REWARD_COIN_VALUE = 5

INVALID_INDEX = {
    'args': {
       "Error: Invalid Index"
    }
}

INITIAL_PEERS = (
    ('localhost',5000),
    ('localhost',5001)
)

GET_CHAIN = {
    'name': "full-chain"
}

def GENERATE_ERROR(data):
    message = '{"error": "' + data + '"}'
    message = str(len(message)) + '~' + message
    return message.encode()

def RECEIVE_BLOCK(block): 
    return {
        'action': 'receive_block',
        'params': [block]
    }

def RECEIVE_TRANSACTION(transaction):
    return {
        'action': 'receive_transactions', 
        'params': transaction,
    }

def TRANSACTION_ADDED(block_index):
    return {
        "Transaction will be added to block {}.".format(block_index)
    }

def CHAIN(chain,length):
    return {
        'chain': chain,
        'length': length
        }

def NODES(nodes):
    return {
        'message': 'Nodes added to peer list.',
        'total_nodes': nodes
    }

def REPLACED(chain):
   return {
        'message': 'Our chain was replaced.',
        'new_chain': chain
    }

def AUTHORITATIVE(chain):
    return {
        'message': 'Our chain is authoritative.',
        'chain': chain
    }

def BLOCK_RECEIVED(index,transactions,proof,previous_hash):
       return{
        'message': "Block retrieved.",
        'index': index,
        'transactions': transactions,
        'proof': proof,
        'previous_hash': previous_hash
    }

def GET_BLOCK(index):
    return {
        'action':"get_block",
        'params': [index]
    }
