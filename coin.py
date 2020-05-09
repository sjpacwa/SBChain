"""
coin.py

"""

# Standard library imports
import json
from uuid import uuid4


class Coin:
    def __init__(self, transaction_id, value, uuid=None):
        self._transaction_id = transaction_id
        self._value = value
        self._uuid = str(uuid4()).replace('-', '') if uuid == None else uuid

    @property
    def get_transaction_id(self):
        return self._transaction_id

    @property
    def get_value(self):
        return self._value

    @property
    def get_uuid(self):
        return self._uuid

    @property
    def to_json(self):
        return {
            'uuid': self._uuid,
            'transaction_id': self._transaction,
            'value': self._value,
        }

    @property
    def to_string(self):
        return json.dumps(self.to_json(), default=str)

def coin_from_json(data):
    return Coin(data['transaction_id'], data['value'], data['uuid'])

def coin_string_string(data):
    return block_from_json(json.loads(data))

