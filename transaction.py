"""
transaction.py

"""

# Standard library imports
import json
import logging
from datetime import datetime
from uuid import uuid4

# Local imports
from coin import Coin, coin_from_json, reward_coin_from_json
from copy import deepcopy
from history import History
from macros import REWARD_COIN_VALUE


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
        self._reward_value = 0
        for recipient in self._outputs:
            for coin in self._outputs[recipient]:
                if recipient == 'SYSTEM':
                    self._reward_value += coin.get_value()
                else:
                    self._output_value += coin.get_value()


    def verify(self):
        """
        verify
        Assumptions:
        1. The transaction history has been checked for duplicates.
        2. Input coins previously existed in the system.
        3. Output coins were created from scratch.
        4. Assume that history is already locked.
        """

        history = History()

        if self._input_value < 0 or self._output_value < 0 or self._reward_value < 0:
            return False

        if self._input_value != (self._output_value + self._reward_value):
            return False

        for coin in self._inputs:
            transaction = history.get_transaction(coin.get_transaction_id())
            if not transaction.check_coin(self._sender, coin):
                return False

        for coin in self.get_all_output_coins():
            if coin.get_transaction_id() != self._uuid:
                return False

        return True

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

    def get_output_coins(self, recipient):
        return deepcopy(self._outputs.get(recipient, []))

    def get_all_output_coins(self):
        coins = []
        for recipient in self._outputs:
            coins.extend(self.get_output_coins(recipient))

        return coins

    def get_all_reward_coins(self):
        return self._outputs.get('SYSTEM')

    def check_coin(self, recipient, coin):
        return coin in self.get_output_coins(recipient)

    def get_values(self):
        return (self._input_value, self._output_value, self._reward_value)

    def get_uuid(self):
        return self._uuid

    def get_sender(self):
        return self._sender

    def get_inputs(self):
        return deepcopy(self._inputs)

    def get_outputs(self):
        return deepcopy(self._outputs)

    def get_timestamp(self):
        return self._timestamp

    def __eq__(self, other):
        if other == None:
            return False

        if not isinstance(other, Transaction):
            return False

        return other.to_string() == self.to_string()


class RewardTransaction(Transaction):
    def __init__(self, inputs, outputs, uuid=None, timestamp=None):
        Transaction.__init__(self, 'SYSTEM', inputs, outputs, uuid, timestamp)

    def add_new_inputs(self, coins):
        for coin in coins:
            self._inputs.append(coin)
            self._input_value += coin.get_value()
        
        self._output_value = self._input_value + REWARD_COIN_VALUE

        for i in self._outputs:
            self._outputs[i][0].set_value(self._output_value)

    def verify(self):
        """
        verify
        Assumptions:
        1. The transaction history has been checked for duplicates.
        2. Input coins previously existed in the system.
        3. Output coins were created from scratch.
        4. Assume that history is already locked.
        """

        history = History()

        if self._input_value < 0 or self._output_value < 0 or self._reward_value < 0:
            return False

        if (self._input_value + REWARD_COIN_VALUE) != (self._output_value + self._reward_value):
            return False

        for coin in self._inputs:
            transaction = history.get_transaction(coin.get_transaction_id())
            if transaction == None or not transaction.check_coin(self._sender, coin):
                return False

        for coin in self.get_all_output_coins():
            if coin.get_transaction_id() != self._uuid:
                return False

        return True


def reward_transaction_from_json(data, inputs, outputs):
    return RewardTransaction(
        inputs,
        outputs,
        data['uuid'],
        data['timestamp']
    )


def transaction_from_json(data, inputs, outputs):
    return Transaction(
        data['sender'],
        inputs,
        outputs,
        data['uuid'],
        data['timestamp']
    )

def transaction_from_string(data, inputs, outputs):
    return transaction_from_json(json.loads(data), inputs, outputs)

def transaction_verify(history, transaction, reward=False):
    if history.get_transaction(transaction['uuid']) != None:
        # The transaction already exists.
        logging.info("Bad transaction: transaction exists")
        return False, None

    # Check input coins
    bad_transaction = False
    input_coins = []
    for coin in transaction['inputs']:
        found_coin = history.get_coin(coin['uuid'])
        if found_coin == None:
            # The input coin does not exist.
            logging.info("Bad transaction: input coins do not exist")
            bad_transaction = True
            break

        if found_coin.get_value() != coin['value'] or found_coin.get_transaction_id() != coin['transaction_id']:
            # The coin does not match what we have in history.
            logging.info("Bad transaction: input coins do not match")

            bad_transaction = True
            break

        input_coins.append(found_coin)

    if bad_transaction:
        return False, None

    # Check output coins
    output_coins = {}
    for recipient in transaction['outputs']:
        if bad_transaction:
            break

        output_coins[recipient] = []

        for coin in transaction['outputs'][recipient]:
            if history.get_coin(coin['uuid']):
                logging.error('Fatal Error: This transaction contains an output coin that already exists: ' + str(transaction))
                bad_transaction = True
                break

            if reward:
                output_coins[recipient].append(reward_coin_from_json(coin))
            else:
                output_coins[recipient].append(coin_from_json(coin))

    if bad_transaction:
        return False, None

    if reward:
        new_transaction = reward_transaction_from_json(transaction, input_coins, output_coins)
    else:
        new_transaction = transaction_from_json(transaction, input_coins, output_coins)

    if new_transaction.verify():
        # The transaction looks proper. Remove inputs and add outputs to history.
        for coin in input_coins:
            history.remove_coin(coin.get_uuid())

        for recipient in output_coins:
            for coin in output_coins[recipient]:
                history.add_coin(coin)

        # Add transaction to queue and history.
        history.add_transaction(new_transaction)
        return True, new_transaction

    logging.info("Bad transaction: built in verification failed")
    return False, None
