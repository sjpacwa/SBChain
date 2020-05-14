"""
transaction.py

"""

# Standard library imports
import json
from datetime import datetime
from uuid import uuid4

# Local imports
from coin import Coin


class Transaction:
    def __init__(self, sender, inputs, outputs, uuid=None, timestamp=None):
        self._uuid = str(uuid4()).replace('-', '') if uuid == None else uuid
        self._timestamp = str(datetime.now()) if timestamp == None else timestamp

        self._sender = sender

        self._inputs = inputs
        self._input_value = 0
        for coin in self._inputs:
            self._input_value += coin.get_value()

        self._outputs = outputs
        self._output_value = 0
        for recipient in self._outputs:
            for coin in self._outputs[recipient]:
                self._output_value += coin.get_value()

        self._reward_value = self._input_value - self._output_value

    def to_json(self):
        return {
            'uuid': self._uuid,
            'timestamp': self._timestamp,
            'sender': self._sender,
            'inputs': [coin.to_json() for coin in self._inputs],
            'outputs': {recipient:[coin.to_json() for coin in self._outputs[recipient]] for recipient in self._outputs},
            'input_value': self._input_value,
            'output_value': self._output_value,
            'reward_value': self._reward_value
        }

    def to_string(self):
        return json.dumps(self.to_json(), default=str)

    def get_coins(self, recipient):
        return self._outputs[recipient].deep_copy()

    def check_coin(self, recipient, coin):
        return coin in self._outputs[recipient]

    def get_values(self):
        return (self._input_value, self._output_value, self._reward_value)

    def get_uuid(self):
        return self._uuid

    def get_sender(self):
        return self._sender

    def get_inputs(self):
        return self._inputs.deep_copy()

    def get_outputs(self):
        return self._outputs.deep_copy()    

    def get_timestamp(self):
        return self._timestamp

def transaction_from_json(data):
    return Transaction(
        data['sender'],
        [coin_from_json(input) for coin in data['inputs']],
        {recipient:[coin_from_json(coin) for coin in data['outputs'][recipient]] for recipient in data['outputs']},
        data['uuid'],
        data['timestamp']
    )

def transaction_from_string(data):
    return transaction_from_json(json.loads(data))

