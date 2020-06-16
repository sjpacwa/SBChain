"""
coin.py

This file holds the Coin object and related helper methods.

2020 Stephen Pacwa and Daniel Okazaki
Santa Clara University
"""

# Standard library imports
import json
from uuid import uuid4


class Coin:
    """
    Coin
    """

    def __init__(self, transaction_id, value, uuid=None):
        """
        __init__()

        The constructor for the Coin object.

        :param transaction_id: <str> The transaction the coin is attached to.
        :param value: <int> The value of the coin.
        :param uuid: <str> The unique identifier for this coin.
        """

        self._transaction_id = transaction_id
        self._value = value
        self._uuid = str(uuid4()).replace('-', '') if uuid is None else uuid

    def get_transaction_id(self):
        """
        get_transaction_id()

        Retrieves the transaction ID of the coin.

        :return: <str> The transaction ID.
        """

        return self._transaction_id

    def get_value(self):
        """
        get_value()

        Retrieves the value of the coin.

        :return: <int> The value.
        """

        return self._value

    def get_uuid(self):
        """
        get_uuid()

        Retrieves the uuid of the coin.

        :return: The UUID.
        """

        return self._uuid

    def to_json(self):
        """
        to_json()

        This returns the JSON object form of the coin.

        :return: <dict> The JSON.
        """

        return {
            'uuid': self._uuid,
            'transaction_id': self._transaction_id,
            'value': self._value,
        }

    def to_string(self):
        """
        to_string()

        This return the JSON string form of the coin.

        :return: <str> The JSON.
        """

        return json.dumps(self.to_json(), default=str)

    def __eq__(self, other):
        """
        __eq__()

        This returns whether or not two coins are equal by comparing
        each field.

        :param other: <Coin Object> the other object to compare.

        :return: <boolean> Whether they are equal or not.
        """

        if other is None:
            return False

        if not isinstance(other, Coin):
            return False

        return (self._transaction_id == other.get_transaction_id()
                and self._value == other.get_value()
                and self._uuid == other.get_uuid())

    def __lt__(self, other):
        """
        __lt__()

        This returns whether this coin is less than the other in value.

        :param other: <Coin Object> The other object to compare.

        :return: <boolean> Whether they are equal or not.
        """

        if other is None:
            raise TypeError

        if not isinstance(other, Coin):
            raise TypeError

        return self._value < other.get_value()


class RewardCoin(Coin):
    """
    RewardCoin
    """

    def __init__(self, transaction_id, value, uuid=None):
        """
        __init__()

        The constructor for the RewardCoin object.

        :param transaction_id: <str> The transaction the coin is
            attached to.
        :param value: <int> The value of the coin.
        :param uuid: <str> The identifier for this coin.
        """

        Coin.__init__(self, transaction_id, value, uuid)

    def set_value(self, value):
        """
        set_value()

        Change the value of the reward coin. This is used when a new
        transaction is added during mining.

        :param value: <int> The new value of the coin.
        """

        self._value = value


def coin_from_json(data):
    """
    coin_from_json()

    Create the Coin object from JSON Object form.

    :param data: <dict> The data to create the coin from.

    :return: The new Coin object.
    """

    return Coin(data['transaction_id'], data['value'], data['uuid'])


def reward_coin_from_json(data):
    """
    reward_coin_from_json()

    Create the RewardCoin object from JSON Object form.

    :param data: <dict> The data to create the coin from.

    :return: The new RewardCoin object.
    """

    return RewardCoin(data['transaction_id'], data['value'], data['uuid'])


def coin_from_string(data):
    """
    coin_from_string()

    Creates the Coin objet from JSON string form.

    :param data: <str> The data to create the coin from.

    :return: The new Coin object.
    """

    return coin_from_json(json.loads(data))
