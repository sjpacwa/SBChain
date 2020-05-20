from tests.constants import *
from coin import Coin
from transaction import Transaction
from tasks import receive_transactions
from json import loads
from queue import Empty

import pytest

@pytest.fixture(scope="module")
def initial_history():
    transaction_id = "0"

    output_coins = {metadata['uuid']: []}
    for i in range(10):
        coin = Coin(transaction_id, 1, str(i))
        output_coins[metadata['uuid']].append(coin)
        metadata['history'].add_coin(coin)

    transaction = Transaction("0", [], output_coins, transaction_id)
    metadata['history'].add_transaction(transaction)

def test_single_valid_transaction(initial_history):
    transaction_data = '''
    [
        {{
            "sender": "{}",
            "uuid": "fakeid",
            "timestamp": "now",
            "inputs": [
                {{
                    "uuid": "0",
                    "value": 1,
                    "transaction_id": "0"
                }}
            ],
            "outputs": {{
                "1": [
                    {{
                        "uuid": "11",
                        "value": 1,
                        "transaction_id": "fakeid"
                    }}
                ]
            }}
        }}
    ]'''.format(metadata['uuid'])

    transaction_data = loads(transaction_data)

    receive_transactions(transaction_data, metadata, queues, connection)

    assert queues['trans'].get(block=False) != None

def test_single_invalid_transaction_no_input_coin(initial_history):
    transaction_data = '''
    [
        {{
            "sender": "{}",
            "uuid": "fakeid",
            "timestamp": "now",
            "inputs": [
                {{
                    "uuid": "-1",
                    "value": 1,
                    "transaction_id": "0"
                }}
            ],
            "outputs": {{
                "1": [
                    {{
                        "uuid": "11",
                        "value": 1,
                        "transaction_id": "fakeid"
                    }}
                ]
            }}
        }}
    ]'''.format(metadata['uuid'])

    transaction_data = loads(transaction_data)

    receive_transactions(transaction_data, metadata, queues, connection)

    with pytest.raises(Empty):
        queues['trans'].get(block=False)

"""
def test_multiple_valid_transactions(initial_history):


def test_multiple_invalid_transactions(initial_history):
"""
    
