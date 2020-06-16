"""
Transaction_test.py

This file tests the Transaction functionality

2020 Stephen Pacwa and Daniel Okazaki
Santa Clara University
"""

# Standard library imports
from json import loads
from queue import Empty
import pytest

# Local imports
from tests.constants import create_metadata, BLANK_TRANSACTION, queues, connection, FakeConnection
from coin import Coin, RewardCoin
from transaction import Transaction, RewardTransaction
from tasks import receive_transactions, new_transaction, receive_transaction_internal
from macros import REWARD_COIN_VALUE
from mine import handle_transactions


pytest.valid_id = 0


@pytest.fixture(scope="module")
def initial_metadata():
    return create_metadata()


@pytest.fixture()
def initial_history(initial_metadata):
    initial_metadata['history'].reset()
    transaction_id = "0"

    pytest.valid_id = 0

    output_coins = {initial_metadata['uuid']: []}
    for i in range(20):
        coin = Coin(transaction_id, 1, str(pytest.valid_id))
        output_coins[initial_metadata['uuid']].append(coin)
        initial_metadata['history'].add_coin(coin)
        pytest.valid_id += 1

    transaction = Transaction(initial_metadata['uuid'], [], output_coins, transaction_id)
    initial_metadata['history'].add_transaction(transaction)


def test_single_valid_transaction(initial_history, initial_metadata):
    transaction_data = BLANK_TRANSACTION(
            initial_metadata['uuid'],
            "fakeid",
            [Coin("0", 1, "0")],
            {"1": [Coin("fakeid", 1, str(pytest.valid_id))]}
    )

    transaction_data = loads(transaction_data)

    receive_transactions([transaction_data], initial_metadata, queues, connection)

    assert queues['trans'].get(block=False) is not None
    with pytest.raises(Empty):
        queues['trans'].get(block=False)


def test_single_invalid_transaction_bad_input_id(initial_history, initial_metadata):
    transaction_data = BLANK_TRANSACTION(
            initial_metadata['uuid'],
            "fakeid2",
            [Coin("0", 1, "-1")],
            {"1": [Coin("fakeid2", 1, str(pytest.valid_id))]}
    )

    transaction_data = loads(transaction_data)

    receive_transactions([transaction_data], initial_metadata, queues, connection)

    with pytest.raises(Empty):
        queues['trans'].get(block=False)


def test_single_invalid_transaction_bad_input_value(initial_history, initial_metadata):
    transaction_data = BLANK_TRANSACTION(
            initial_metadata['uuid'],
            "fakeid11",
            [Coin("0", 2, "2")],
            {"1": [Coin("fakeid11", 1, str(pytest.valid_id))]}
    )

    transaction_data = loads(transaction_data)

    receive_transactions([transaction_data], initial_metadata, queues, connection)

    with pytest.raises(Empty):
        queues['trans'].get(block=False)


def test_single_invalid_transaction_bad_input_transaction_id(initial_history, initial_metadata):
    transaction_data = BLANK_TRANSACTION(
            initial_metadata['uuid'],
            "fakeid12",
            [Coin("3", 1, "2")],
            {"1": [Coin("fakeid12", 1, str(pytest.valid_id))]}
    )

    transaction_data = loads(transaction_data)

    receive_transactions([transaction_data], initial_metadata, queues, connection)

    with pytest.raises(Empty):
        queues['trans'].get(block=False)


def test_single_invalid_transaction_nonmatching_input_coin(initial_history, initial_metadata):
    transaction_data = BLANK_TRANSACTION(
            initial_metadata['uuid'],
            "fakeid3",
            [Coin("0", 3, "2")],
            {"1": [Coin("fakeid3", 1, str(pytest.valid_id))]}
    )

    transaction_data = loads(transaction_data)

    receive_transactions([transaction_data], initial_metadata, queues, connection)

    with pytest.raises(Empty):
        queues['trans'].get(block=False)


def test_single_invalid_transaction_output_higher_than_input(initial_history, initial_metadata):
    transaction_data = BLANK_TRANSACTION(
            initial_metadata['uuid'],
            "fakeid4",
            [Coin("0", 1, "3")],
            {"1": [Coin("fakeid4", 2, str(pytest.valid_id))]}
    )

    transaction_data = loads(transaction_data)

    receive_transactions([transaction_data], initial_metadata, queues, connection)

    with pytest.raises(Empty):
        queues['trans'].get(block=False)


def test_single_invalid_transaction_reused_input_coin(initial_history, initial_metadata):
    valid_transaction_data = BLANK_TRANSACTION(
            initial_metadata['uuid'],
            "fakeid5",
            [Coin("0", 1, "1")],
            {"1": [Coin("fakeid5", 1, str(pytest.valid_id))]}
    )

    valid_transaction_data = loads(valid_transaction_data)
    receive_transactions([valid_transaction_data], initial_metadata, queues, connection)
    assert queues['trans'].get(block=False) is not None

    invalid_transaction_data = BLANK_TRANSACTION(
            initial_metadata['uuid'],
            "fakeid6",
            [Coin("0", 1, "1")],
            {"1": [Coin("fakeid6", 1, str(pytest.valid_id + 1))]}
    )

    invalid_transaction_data = loads(invalid_transaction_data)

    receive_transactions([invalid_transaction_data], initial_metadata, queues, connection)

    with pytest.raises(Empty):
        queues['trans'].get(block=False)


def test_single_invalid_transaction_reused_output_coin(initial_history, initial_metadata):
    valid_transaction_data = BLANK_TRANSACTION(
            initial_metadata['uuid'],
            "fakeid7",
            [Coin("0", 1, "2")],
            {"1": [Coin("fakeid7", 1, str(pytest.valid_id))]}
    )

    valid_transaction_data = loads(valid_transaction_data)
    receive_transactions([valid_transaction_data], initial_metadata, queues, connection)
    assert queues['trans'].get(block=False) is not None

    invalid_transaction_data = BLANK_TRANSACTION(
            initial_metadata['uuid'],
            "fakeid8",
            [Coin("0", 1, "3")],
            {"1": [Coin("fakeid8", 1, "13")]}
    )

    invalid_transaction_data = loads(invalid_transaction_data)

    receive_transactions([invalid_transaction_data], initial_metadata, queues, connection)

    with pytest.raises(Empty):
        queues['trans'].get(block=False)


def test_json_serializable(initial_history, initial_metadata):
    valid_transaction_data = BLANK_TRANSACTION(
            initial_metadata['uuid'],
            "fakeid9",
            [Coin("0", 1, "1")],
            {"1": [Coin("fakeid9", 1, str(pytest.valid_id))]}
    )

    valid_transaction_data = loads(valid_transaction_data)
    receive_transactions([valid_transaction_data], initial_metadata, queues, connection)
    assert queues['trans'].get(block=False) is not None

    invalid_transaction_data = BLANK_TRANSACTION(
            initial_metadata['uuid'],
            "fakeid10",
            [Coin("0", 1, "1")],
            {"1": [Coin("fakeid10", 1, "14")]}
    )

    invalid_transaction_data = loads(invalid_transaction_data)

    response = receive_transaction_internal([invalid_transaction_data], initial_metadata, queues)

    for message in response:
        assert loads(message)
    with pytest.raises(Empty):
        queues['trans'].get(block=False)


def test_multiple_valid_transactions(initial_history, initial_metadata):
    transactions = []
    for i in range(3):
        transactions.append(BLANK_TRANSACTION(initial_metadata['uuid'], "validid" + str(i), [Coin("0", 1, str(i))],
                                            {"1": [Coin("validid" + str(i), 1, str(pytest.valid_id + i))]}))

    all_transactions = '[' + ', '.join(transactions) + ']'
    all_transactions = loads(all_transactions)

    receive_transactions(all_transactions, initial_metadata, queues, connection)

    assert queues['trans'].get(block=False) is not None
    assert queues['trans'].get(block=False) is not None
    assert queues['trans'].get(block=False) is not None
    with pytest.raises(Empty):
        queues['trans'].get(block=False)


def test_multiple_invalid_transactions(initial_history, initial_metadata):
    transactions = []
    for i in range(2):
        transactions.append(BLANK_TRANSACTION(initial_metadata['uuid'], "invalidid" + str(pytest.valid_id), [Coin("0", 1, str(i))],
                                            {"1": [Coin("invalidid" + str(i), 1, str(pytest.valid_id + i))]}))

    transactions.append(transactions[1])

    all_transactions = '[' + ', '.join(transactions) + ']'
    all_transactions = loads(all_transactions)

    receive_transactions(all_transactions, initial_metadata, queues, connection)

    with pytest.raises(Empty):
        queues['trans'].get(block=False)


def test_new_transaction(initial_history, initial_metadata):
    new_transaction({'input': 2.5, 'output': {'A': 1, 'B': 0.5}}, initial_metadata, queues, FakeConnection())

    assert queues['trans'].get(block=False) is not None
    with pytest.raises(Empty):
        queues['trans'].get(block=False)


def test_bad_new_transaction_small_input(initial_history, initial_metadata):
    new_transaction({'input': 0.5, 'output': {'A': 1, 'B': 0.5}}, initial_metadata, queues, FakeConnection())

    with pytest.raises(Empty):
        queues['trans'].get(block=False)


def test_bad_new_transaction_large_input(initial_history, initial_metadata):
    new_transaction({'input': 1000, 'output': {'A': 1, 'B': 0.5}}, initial_metadata, queues, FakeConnection())

    with pytest.raises(Empty):
        queues['trans'].get(block=False)


def test_verify_multiple_transactions(initial_history, initial_metadata):
    for i in range(5):
        new_transaction({'input': 1, 'output': {'A': 1}}, initial_metadata, queues, FakeConnection())

    reward_transaction = RewardTransaction([],
                                            {initial_metadata['uuid']: [RewardCoin('REWARD_ID', REWARD_COIN_VALUE)]},
                                            'REWARD_ID')
    for i in range(5):
        handle_transactions(initial_metadata, queues, reward_transaction)

        assert queues['tasks'].get(block=False) is not None
        with pytest.raises(Empty):
            queues['tasks'].get(block=False)
