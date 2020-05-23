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
    transaction_data = BLANK_TRANSACTION(
            metadata['uuid'],
            "fakeid",
            [Coin("0", 1, "0")],
            {"1": [Coin("fakeid", 1, "11")]}
    )

    print(transaction_data)

    transaction_data = loads(transaction_data)

    receive_transactions([transaction_data], metadata, queues, connection)

    assert queues['trans'].get(block=False) != None
    with pytest.raises(Empty):
        queues['trans'].get(block=False)


def test_single_invalid_transaction_bad_input_id(initial_history):
    transaction_data = BLANK_TRANSACTION(
            metadata['uuid'],
            "fakeid2",
            [Coin("0", 1, "-1")],
            {"1": [Coin("fakeid2", 1, "11")]}
    )

    transaction_data = loads(transaction_data)

    receive_transactions([transaction_data], metadata, queues, connection)

    with pytest.raises(Empty):
        queues['trans'].get(block=False)


def test_single_invalid_transaction_bad_input_value(initial_history):
    transaction_data = BLANK_TRANSACTION(
            metadata['uuid'],
            "fakeid11",
            [Coin("0", 2, "2")],
            {"1": [Coin("fakeid11", 1, "11")]}
    )

    transaction_data = loads(transaction_data)

    receive_transactions([transaction_data], metadata, queues, connection)

    with pytest.raises(Empty):
        queues['trans'].get(block=False)


def test_single_invalid_transaction_bad_input_transaction_id(initial_history):
    transaction_data = BLANK_TRANSACTION(
            metadata['uuid'],
            "fakeid12",
            [Coin("3", 1, "2")],
            {"1": [Coin("fakeid12", 1, "11")]}
    )

    transaction_data = loads(transaction_data)

    receive_transactions([transaction_data], metadata, queues, connection)

    with pytest.raises(Empty):
        queues['trans'].get(block=False)


def test_single_invalid_transaction_nonmatching_input_coin(initial_history):
    transaction_data = BLANK_TRANSACTION(
            metadata['uuid'],
            "fakeid3",
            [Coin("0", 3, "2")],
            {"1": [Coin("fakeid3", 1, "12")]}
    )

    transaction_data = loads(transaction_data)

    receive_transactions([transaction_data], metadata, queues, connection)

    with pytest.raises(Empty):
        queues['trans'].get(block=False)


def test_single_invalid_transaction_output_higher_than_input(initial_history):
    transaction_data = BLANK_TRANSACTION(
            metadata['uuid'],
            "fakeid4",
            [Coin("0", 1, "3")],
            {"1": [Coin("fakeid4", 2, "12")]}
    )

    transaction_data = loads(transaction_data)

    receive_transactions([transaction_data], metadata, queues, connection)

    with pytest.raises(Empty):
        queues['trans'].get(block=False)


def test_single_invalid_transaction_reused_input_coin(initial_history):
    history = History()
    print(history.instance.coins)
    valid_transaction_data = BLANK_TRANSACTION(
            metadata['uuid'],
            "fakeid5",
            [Coin("0", 1, "1")],
            {"1": [Coin("fakeid5", 1, "12")]}
    )

    valid_transaction_data = loads(valid_transaction_data)
    receive_transactions([valid_transaction_data], metadata, queues, connection)
    assert queues['trans'].get(block=False) != None

    invalid_transaction_data = BLANK_TRANSACTION(
            metadata['uuid'],
            "fakeid6",
            [Coin("0", 1, "1")],
            {"1": [Coin("fakeid6", 1, "13")]}
    )

    invalid_transaction_data = loads(invalid_transaction_data)

    receive_transactions([invalid_transaction_data], metadata, queues, connection)

    with pytest.raises(Empty):
        queues['trans'].get(block=False)


def test_single_invalid_transaction_reused_output_coin(initial_history):
    history = History()
    print(history.instance.coins)
    valid_transaction_data = BLANK_TRANSACTION(
            metadata['uuid'],
            "fakeid7",
            [Coin("0", 1, "2")],
            {"1": [Coin("fakeid7", 1, "13")]}
    )

    valid_transaction_data = loads(valid_transaction_data)
    receive_transactions([valid_transaction_data], metadata, queues, connection)
    assert queues['trans'].get(block=False) != None

    invalid_transaction_data = BLANK_TRANSACTION(
            metadata['uuid'],
            "fakeid8",
            [Coin("0", 1, "3")],
            {"1": [Coin("fakeid8", 1, "13")]}
    )

    invalid_transaction_data = loads(invalid_transaction_data)

    receive_transactions([invalid_transaction_data], metadata, queues, connection)

    with pytest.raises(Empty):
        queues['trans'].get(block=False)


def test_single_invalid_transaction_output_higher_than_input(initial_history):
    transaction_data = BLANK_TRANSACTION(
            metadata['uuid'],
            "fakeid9",
            [Coin("0", 1, "3")],
            {"1": [Coin("fakeid10", 2, "12")]}
    )

    transaction_data = loads(transaction_data)

    receive_transactions([transaction_data], metadata, queues, connection)

    with pytest.raises(Empty):
        queues['trans'].get(block=False)


def test_multiple_valid_transactions(initial_history):
    transactions = []
    for i in range(3):
        transactions.append(BLANK_TRANSACTION(metadata['uuid'],
            "validid" + str(i),
            [Coin("0", 1, str(i + 4))],
            {"1": [Coin("validid" + str(i), 1, str(i + 20))]}))

    all_transactions = '[' + ', '.join(transactions) + ']'
    all_transactions = loads(all_transactions)

    receive_transactions(all_transactions, metadata, queues, connection)

    assert queues['trans'].get(block=False) != None
    assert queues['trans'].get(block=False) != None
    assert queues['trans'].get(block=False) != None
    with pytest.raises(Empty):
        queues['trans'].get(block=False)


def test_multiple_invalid_transactions(initial_history):
    transactions = []
    for i in range(2):
        transactions.append(BLANK_TRANSACTION(metadata['uuid'],
            "invalidid" + str(i),
            [Coin("0", 1, str(i + 7))],
            {"1": [Coin("invalidid" + str(i), 1, str(i + 30))]}))

    transactions.append(transactions[1])

    all_transactions = '[' + ', '.join(transactions) + ']'
    all_transactions = loads(all_transactions)

    receive_transactions(all_transactions, metadata, queues, connection)

    assert queues['trans'].get(block=False) != None
    assert queues['trans'].get(block=False) != None
    with pytest.raises(Empty):
        queues['trans'].get(block=False)
    
