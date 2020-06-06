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

INITIAL_PEERS = [
    ('localhost',5000),
    ('localhost',5001)
    ]


def GENERATE_ERROR(data):
    message = '{"error": "' + data + '"}'
    message = str(len(message)) + '~' + message
    return message.encode()


def RECEIVE_BLOCK(block, host, port): 
    return {
        'action': 'receive_block',
        'params': [block, host, port]
    }


def RECEIVE_TRANSACTION(transaction):
    return {
        'action': 'receive_transactions', 
        'params': transaction,
    }


def REGISTER_NODES(peer_list):
    return {"action": "register_nodes", "params": [peer_list]}


def TRANSACTION_ADDED(block_index):
    return {
        "Transaction will be added to block {}.".format(block_index)
    }


def GET_CHAIN():
    return {'action': 'get_chain', 'params': []}


def GET_CHAIN_PAGINATED(size):
    return {'action': 'get_chain_paginated', 'params': [size]}


def GET_CHAIN_PAGINATED_ACK():
    return {'action': 'inform', 'params': {'message': 'ACK'}}


def GET_CHAIN_PAGINATED_STOP():
    return {'action': 'inform', 'params': {'message': 'STOP'}}


def SEND_CHAIN(chain, length):
    return {'chain': chain, 'length': length}


def SEND_CHAIN_SECTION(section, status):
    return {'section': section, 'status': status}


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
