from threading import Lock
from uuid import uuid4
from queue import Queue

from blockchain import Blockchain
from history import History

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

connection = None
