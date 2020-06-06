import json
from threading import Lock
from uuid import uuid4
from queue import Queue

from blockchain import Blockchain
from block import Block
from encoder import ComplexEncoder
from history import History
from transaction import Transaction

uuid = str(uuid4()).replace("-", "")

def create_metadata(host='127.0.0.1', port=5000, blockchain=Blockchain()):
    history = History(uuid)
    

    return {
        'host': host,
        'port': port,
        'done': Lock(),
        'uuid': uuid,
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


class FakeConnection():
    def __init__(self):
        self.data = None
        self.changed = False
        self.sent = False

    def getpeername(self):
        return ('127.0.0.1', 5000)

    def send(self, data):
        while self.sent:
            pass
        split_data = data.decode().split('~')
        self.data = json.loads(split_data[1])
        self.sent = True

    def recv(self, size):
        while not self.changed:
            pass
        self.changed = False
        return self.data

    def read_data(self):
        while not self.sent:
            pass
        self.sent = False
        return self.data

    def set_data(self, data):
        while self.changed:
            pass

        json_message = json.dumps(data)
        full_data = str(len(json_message)) + '~' + json_message
        print(full_data)
        self.data = full_data.encode()
        self.changed = True


class FakeBlockchain():
    def __init__(self, length):
        self.chain = []
        self.version_number = 0

        for i in range(length):
            self.chain.append(["This is fake block number " + str(i)])

    def get_chain(self):
        return self.chain

    def get_version_number(self):
        return self.version_number

    def increment_version_number(self):
        self.version_number += 1

