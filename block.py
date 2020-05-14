"""
block.py

This file defines the Block class which is used to hold information on 
a block that is stored in the blockchain.
"""

# Standard library imports
import hashlib
import json
import logging
from datetime import datetime


class Block:
    """
    Block
    """
    def __init__(self, index, transactions, proof, previous_hash, timestamp=-1):
        """
        __init__
        
        The constructor for a Block object.

        :param index: <int> The index of the block.
        :param transactions: <list> A list of transactions in the block.
        :param proof: <str> The proof of the block.
        :param previous_hash: <str> The hash of the previous block.
        :param timestamp: <datetime> The datetime of block creation. It 
            is set to datetime.min for the genesis block.
        """

        self.index = index
        self.transactions = transactions
        self.proof = proof
        self.previous_hash = previous_hash
        self.timestamp = datetime.min.strftime('%Y-%m-%dT%H:%M:%SZ') if timestamp == -1 else timestamp
    @property
    def to_json(self):
        """
        to_json

        Not Thread Safe

        Converts a Block object into JSON-object form, (i.e. it is 
        composed of dictionaries and lists).

        :returns: <dict> JSON-object form of Block.
        """
        
        return {
            'index': self.index,
            'previous_hash': self.previous_hash,
            'proof': self.proof,
            'timestamp': self.timestamp,
            'transactions': [transaction.to_json() for transaction in self.transactions]
        }
    @property
    def to_string(self):
        """
        to_string

        Not Thread Safe

        Converts a Block object into JSON-string form, (i.e. it is 
        composed of a string). The resulting string is always ordered.

        :returns: <str> JSON-string form of Block.
        """

        return json.dumps(
            self.to_json,
            default=str
        )
    @property
    def hash(self):
        """
        hash

        Not Thread Safe

        Creates a SHA-256 hash of a Block from its string form.
        """
        
        return hashlib.sha256(self.to_string.encode()).hexdigest()

    def __eq__(self, other):
        """
        __eq__

        Not Thread Safe

        Checks to see if two Blocks are equal.

        :param other: <Block Object> The Block to compare to.
        """
        return (self.index == other.index
            and self.timestamp == other.timestamp
            and self.transactions == other.transactions
            and self.proof == other.proof
            and self.previous_hash == other.previous_hash)


def block_from_json(data):
    """
    block_from_json

    Converts a JSON-object form into a Block object.

    :param data: <dict> The JSON-object form of a block.
    :returns: <Block Object> A new object.

    :raises: <KeyError> If the proper keys have not been supplied.
    """

    # Check that the proper keys have been provided.
    necessary_keys = [
        'index',
        'transactions',
        'proof',
        'previous_hash',
        'timestamp'
    ]

    for key in necessary_keys:
        if key not in data:
            raise KeyError('{} not found during block creation'.format(key))

    return Block(
        data['index'],
        [transaction_from_json(transaction) for transaction in data['transactions']],
        data['proof'],
        data['previous_hash'],
        data['timestamp']
    )


def block_from_string(data):
    """
    block_from_string

    Converts a JSON-string form into a Block object.

    :param data: <str> The JSON-string form of a block.
    
    :returns: <Block Object> A new object.

    """

    return block_from_json(json.loads(data))

