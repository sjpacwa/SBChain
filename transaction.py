"""
transaction.py

This file holds the transaction object and the related helper functions.
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
    """
    Transaction
    """

    def __init__(self, sender, inputs, outputs, uuid=None, timestamp=None):
        """
        __init__()

        The constructor for the transaction object.

        :param sender: <str> The UUID of the sender node.
        :param inputs: <list<Coin Object>> The coins that are being consumed.
        :param outputs: <dict<<str>, <list<Coin Object>>> The coins that are
            being produced and their owners.
        :param uuid: <str> The UUID of this transaction.
        :param timestamp: <str> The time that this transaction was made.
        """

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


    def verify(self, history=None):
        """
        verify()
        
        This function verifies if a tranaction is valid.

        Assumptions:
        1. The transaction history has been checked for duplicates.
        2. Input coins previously existed in the system.
        3. Output coins were created from scratch.
        4. Assume that history is already locked.

        :param history: <History Object> A place where a history object can be 
            passed in to be used.

        :return: Whether the transaction is valid or not.
        """

        if history is None:
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
        """
        to_json()

        This function converts the object form to JSON Object form.

        :return: <dict> The JSON Object form of the Transaction.
        """

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
        """
        to_string()

        This function converts the object form to JSON string form.

        :return: <str> The JSON String form of the Transaction.
        """
        return json.dumps(self.to_json(), default=str)

    def get_output_coins(self, recipient):
        """
        get_output_coins()

        This function retrieves the output coins of a recipient.

        :param recipient: <str> The recipient whose coins are needed.

        :return: <list<Coin Object>> The coins.
        """

        return deepcopy(self._outputs.get(recipient, []))

    def get_all_output_coins(self):
        """
        get_all_output_coins()

        This function retrieves all the output coins in the transaction.

        :return: <list<Coin Object>> All the output coins.
        """

        coins = []
        for recipient in self._outputs:
            coins.extend(self.get_output_coins(recipient))

        return coins

    def get_all_output_recipient_coins(self):
        """
        get_all_output_recipient_coins()

        This function retrieves all the output coins with recipients.

        :return: <dict<<str>, <list<CoinObject>>> The output coins.
        """

        return self._outputs

    def get_all_reward_coins(self):
        """
        get_all_reward_coins()

        This function retrieves all the coins that are rewards. I.e. due
        to SYSTEM.

        :return: <list<Coin Object>> The reward coins.
        """

        return self._outputs.get('SYSTEM')

    def check_coin(self, recipient, coin):
        """
        check_coin()

        This function checks whether or not a specific coin matches what is
        stored in the transaction.
        
        :param recipient: <str> The recipient of the coin.
        :param coin: <Coin Object> The coin to check.

        :return: <boolean> Whether or not the coin exists and matches.
        """

        return coin in self.get_output_coins(recipient)

    def get_values(self):
        """
        get_values()

        This function retrieves the three different values of the transaction.
        The input, output, and reward.

        :return: <tuple<str>, <str>, <str>> The values.
        """

        return (self._input_value, self._output_value, self._reward_value)

    def get_uuid(self):
        """
        get_uuid()

        This function retrieves the UUID of the transaction.

        :return: <str> The UUID.
        """

        return self._uuid

    def get_sender(self):
        """
        get_sender()

        This function retrives the original sender of this transaction.

        :return: <str> The ID of the sender.
        """

        return self._sender

    def get_inputs(self):
        """
        get_inputs()

        This function retrives the input coins of the transaction as a copy.

        :return: <list<Coin Object>> A list of the input coins.
        """

        return deepcopy(self._inputs)

    def get_outputs(self):
        """
        get_outputs()

        This function retrieves the output coins of the transaction as a copy.

        :return <dict<<str>, <list<Coin Object>>> The output coins.
        """

        return deepcopy(self._outputs)

    def get_timestamp(self):
        """
        get_timestamp()

        This function retrieves the timestamp the transaction was created.

        :return: <str> The timestamp of the coin.
        """

        return self._timestamp

    def __eq__(self, other):
        """
        __eq__()

        This function checks to see if two transactions are equal.

        :param other: <Transaction Object> The other transaction to check.

        :return: <boolean> Whether the transactions are equal.
        """

        if other == None:
            return False

        if not isinstance(other, Transaction):
            return False

        return other.to_string() == self.to_string()


class RewardTransaction(Transaction):
    """
    RewardTransaction
    """

    def __init__(self, inputs, outputs, uuid=None, timestamp=None):
        """
        __init__()

        The constructor for the RewardTransaction Object.

        :param inputs: <list<Coin Object>> The list of inputs.
        :param outputs: <dict<<str>, <list<Coin Objects>>> The outputs.
        :param uuid: <str> The UUID of the new transaction.
        :param timestamp: <str> The timestamp of the transaction at time of creation.
        """

        Transaction.__init__(self, 'SYSTEM', inputs, outputs, uuid, timestamp)

    def add_new_inputs(self, coins):
        """
        add_new_inputs()

        This function allows new input coins to be added to the transaction.

        :param coins: <list<Coin Object>> A list of the new input coins.
        """
        for coin in coins:
            self._inputs.append(coin)
            self._input_value += coin.get_value()
        
        self._output_value = self._input_value + REWARD_COIN_VALUE

        for i in self._outputs:
            self._outputs[i][0].set_value(self._output_value)

    def verify(self, history=None):
        """
        verify()
 
        This function verifies if a tranaction is valid.

        Assumptions:
        1. The transaction history has been checked for duplicates.
        2. Input coins previously existed in the system.
        3. Output coins were created from scratch.
        4. Assume that history is already locked.

        :param history: <History Object> A place where a history object can be 
            passed in to be used.

        :return: Whether the transaction is valid or not.
        """

        if history is None:
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


def inputs_from_json(inputs):
    """
    inputs_from_json()

    This function creates Coin Objects from JSON Object form.

    :param inputs: <list<dict>> A list of the coins in JSON.

    :return: <list<Coin Object>> A list of Coins.
    """

    obj_inputs = []

    for input_coin in inputs:
        obj_inputs.append(coin_from_json(input_coin))

    return obj_inputs


def outputs_from_json(outputs, reward=False):
    """
    outputs_from_json

    This function creates Coin Objects from JSON Object form.

    :param outputs: <dict<<str>, <list<dict>>> The output coins in
        JSON Object form.
    :param reward: <boolean> Whether to make RewardCoins or not.

    :return: <dict<<str>, <list<Coin Object>>> The output coins as objects.
    """

    obj_outputs = {}
    
    for recipient in outputs:
        obj_outputs[recipient] = []
        for output_coin in outputs[recipient]:
            if reward:
                obj_outputs[recipient].append(reward_coin_from_json(output_coin))
            else:
                obj_outputs[recipient].append(coin_from_json(output_coin))

    return obj_outputs


def reward_transaction_from_json(data):
    """
    reward_transaction_from_json()

    This function converts JSON Object form to a RewardTransaction.

    :param data: <dict> The JSON Object form of the transaction.

    :return: <RewardTransaction> The new RewardTransaction.
    """

    return RewardTransaction(
        inputs_from_json(data['inputs']),
        outputs_from_json(data['outputs'], True),
        data['uuid'],
        data['timestamp']
    )


def transaction_from_json(data):
    """
    transaction_from_json()

    This function converts JSON Object form to a Transaction.

    :param data: <dict> The JSON Object form of the tramsaction.

    :return: <Transaction> The new Transaction.
    """

    return Transaction(
        data['sender'],
        inputs_from_json(data['inputs']),
        outputs_from_json(data['outputs']),
        data['uuid'],
        data['timestamp']
    )

def transaction_from_string(data, inputs, outputs):
    """
    transaction_from_string()

    This function converts JSON string form to a Transaction.

    :param data: <dict> The JSON string form of the Transaction.

    :return: <Transaction> The new Transaction.
    """

    return transaction_from_json(json.loads(data))

def transaction_verify(history, transaction, reward=False):
    """
    transaction_verify()

    This function verifies a transaction in several ways.

    :param history: <History Object> The history object to use.
    :param transaction: <Transaction> The transaction to check.
    :param reward: <boolean> Whether this is a reward transaction or not.

    :return: <boolean> Whether the transaction passes verification.
    """

    if history.get_transaction(transaction.get_uuid()) != None:
        # The transaction already exists.
        logging.info("Bad transaction: transaction exists")
        return False

    # Check input coins
    bad_transaction = False
    for coin in transaction.get_inputs():
        found_coin = history.get_coin(coin.get_uuid())
        if found_coin == None:
            # The input coin does not exist.
            logging.info("Bad transaction: input coins do not exist")
            bad_transaction = True
            break

        if found_coin.get_value() != coin.get_value() or found_coin.get_transaction_id() != coin.get_transaction_id():
            # The coin does not match what we have in history.
            logging.info("Bad transaction: input coins do not match")

            bad_transaction = True
            break

    if bad_transaction:
        return False

    # Check output coins
    for recipient in transaction.get_all_output_recipient_coins():
        if bad_transaction:
            break


        for coin in transaction.get_all_output_recipient_coins()[recipient]:
            if history.get_coin(coin.get_uuid()):
                logging.error('Fatal Error: This transaction contains an output coin that already exists: ' + str(transaction))
                bad_transaction = True
                break


    if bad_transaction:
        return False


    if transaction.verify(history):
        # The transaction looks proper. Remove inputs and add outputs to history.
        for coin in transaction.get_inputs():
            history.remove_coin(coin.get_uuid())

        for coin in transaction.get_all_output_coins():
            history.add_coin(coin)

        # Add transaction to queue and history.
        history.add_transaction(transaction)
        return True

    logging.info("Bad transaction: built in verification failed")
    return False

