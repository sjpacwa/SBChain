THREAD_FUNCTIONS = {
	"receive_block": self.receive_block,
	"broadcast": self.broadcast,
	"broadcast_all": self.broadcast_all,
    "request_result": self.request_result,
    "new_transaction": self.new_transaction,
    "receieve_transaction": self.receive_transaction,
    "full_chain": self.full_chain,
    "register_nodes": self.register_nodes,
    "consensus": self.consensus,
    "get_block": self.get_block
}

NO_INDEX_FOUND = {
    'name': 'broadcast',
    'args': {
       "Error: No Index found"
    }
}

INVALID_INDEX = {
    'name': 'broadcast',
    'args': {
       "Error: Invalid Index"
    }
}

def BROADCAST_ALL_RECEIVE_BLOCK(block):
    return {
        'name': 'broadcast_all',
	    'args': {
		    'name': 'receieve_block',
		    'args': block
        }
    }

def BROADCAST_ALL_RECEIVE_TRANSACTION(transaction):
    return {
        'name': 'broadcast_all',
        'args': {
            'name': 'receieve_transactions', 
            'args': {
                'sender': transaction['sender'],
                'recipient': transaction['recipient'],
                'amount': transaction['amount'],
                'timestamp': transaction['timestamp']
            }
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