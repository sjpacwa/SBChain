"""
blockchain.py

This file defines the Blockchain class which is used to manage information 
related to the chain.
"""

NO_INDEX_FOUND = {
    'name': 'broadcast',
    'args': {
       "Error: No Index found"
    }
}

INVALID_INDEX = {
    'args': {
       "Error: Invalid Index"
    }
}

NEIGHBORS = (
    ('localhost',5000),
    ('localhost',5001)
)

GET_CHAIN = {
    'name': "full-chain"
}

def RECEIVE_BLOCK(block):
    return {
        'name': 'receive_block',
        'args': block
    }

def RECEIVE_TRANSACTION(transaction):
    return {
        'name': 'receive_transactions', 
        'args': {
                'sender': transaction['sender'],
                'recipient': transaction['recipient'],
                'amount': transaction['amount'],
                'timestamp': transaction['timestamp']
            }
    }

def TRANSACTION_ADDED(block_index):
    return {
        "Transaction will be added to block {}.".format(block_index)
    }

def TRANSACTION(sender,recipient,amount,timestamp):
    return {
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
            'timestamp': timestamp
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
        'name':"get_block",
        'args': index
    }