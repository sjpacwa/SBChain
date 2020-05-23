import json
from threading import Lock
from uuid import uuid4
from queue import Queue

from blockchain import Blockchain
from encoder import ComplexEncoder
from history import History
from transaction import Transaction

metadata = {
    'host': '127.0.0.1',
    'port': 5000,
    'done': Lock(),
    'uuid': str(uuid4()).replace('-', ''),
    'debug': True,
    'blockchain': Blockchain(),
    'history': History(),
    'peers': [],
    
}

queues = {
    'tasks': Queue(),
    'trans': Queue(),
    'blocks': Queue(),
}

def BLANK_TRANSACTION(sender, uuid, inputs, outputs):

    trans = Transaction(sender, inputs, outputs, uuid, "now")

    return json.dumps(trans, cls=ComplexEncoder)

connection = None
