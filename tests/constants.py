import json
from threading import Lock
from uuid import uuid4
from queue import Queue

from blockchain import Blockchain
from block import Block
from encoder import ComplexEncoder
from history import History
from transaction import Transaction

def create_metadata(host='127.0.0.1', port=5000, blockchain=Blockchain(), history=History()):
    return {
        'host': host,
        'port': port,
        'done': Lock(),
        'uuid': str(uuid4()).replace('-', ''),
        'debug': True,
        'blockchain': blockchain,
        'history': history,
        'peers': []
    }

queues = {
    'tasks': Queue(),
    'trans': Queue(),
    'blocks': Queue(),
}

def BLANK_TRANSACTION(sender, uuid, inputs, outputs):

    trans = Transaction(sender, inputs, outputs, uuid, "now")

    return json.dumps(trans, cls=ComplexEncoder)

def BLANK_BLOCK(index, transactions, proof, previous_hash):
    block = Block(index, transactions, proof, previous_hash)

    return json.dumps(block, cls=ComplexEncoder)

connection = None
