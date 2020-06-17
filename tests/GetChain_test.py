"""
GetChain_test.py

This test is responsible for testing the get chain and get paginated
chain functionality.

2020 Stephen Pacwa and Daniel Okazaki
Santa Clara University
"""

# Standard library imports
from threading import Thread

# Local imports
from tasks import get_chain, get_chain_paginated
from tests.constants import FakeBlockchain, FakeConnection, create_metadata

# Third party imports
import pytest


@pytest.fixture()
def initial_data():
    blockchain = FakeBlockchain(20)
    return (blockchain, create_metadata(blockchain=blockchain))


@pytest.fixture()
def fake_socket():
    return FakeConnection()


def test_get_chain(fake_socket, initial_data):
    blockchain = initial_data[0]
    metadata = initial_data[1]

    get_chain(metadata, None, fake_socket)

    data = fake_socket.read_data()

    assert data['chain'] == blockchain.get_chain()
    assert data['length'] == len(blockchain.get_chain())


def test_paginated_chain_multiple(fake_socket, initial_data):
    blockchain = initial_data[0]
    metadata = initial_data[1]

    thread = Thread(target=get_chain_paginated, args=(4, metadata, None, fake_socket), daemon=True)
    thread.start()

    data = fake_socket.read_data()

    total_list = data['section']
    assert data['status'] == 'INITIAL'

    while True:
        fake_socket.set_data({"action": "inform", "params": {"message": "ACK"}})

        data = fake_socket.read_data()

        total_list = data['section'] + total_list

        if data['status'] == 'FINISHED':
            break

        assert data['status'] == 'CONTINUE'

    assert total_list == blockchain.get_chain()
    assert data['status'] == 'FINISHED'


def test_paginated_chain_non_multiple(fake_socket, initial_data):
    blockchain = initial_data[0]
    metadata = initial_data[1]

    thread = Thread(target=get_chain_paginated, args=(3, metadata, None, fake_socket), daemon=True)
    thread.start()

    data = fake_socket.read_data()

    total_list = data['section']
    assert data['status'] == 'INITIAL'

    while True:
        fake_socket.set_data({"action": "inform", "params": {"message": "ACK"}})

        data = fake_socket.read_data()

        total_list = data['section'] + total_list

        if data['status'] == 'FINISHED':
            break

        assert data['status'] == 'CONTINUE'

    assert total_list == blockchain.get_chain()
    assert data['status'] == 'FINISHED'


def test_paginated_chain_larger(fake_socket, initial_data):
    blockchain = initial_data[0]
    metadata = initial_data[1]

    thread = Thread(target=get_chain_paginated, args=(30, metadata, None, fake_socket), daemon=True)
    thread.start()

    data = fake_socket.read_data()

    assert data['section'] == blockchain.get_chain()
    assert data['status'] == 'FINISHED'


def test_paginated_chain_zero(fake_socket, initial_data):
    metadata = initial_data[1]

    thread = Thread(target=get_chain_paginated, args=(0, metadata, None, fake_socket), daemon=True)
    thread.start()

    data = fake_socket.read_data()

    assert data['section'] == []
    assert data['status'] == 'ERROR'


def test_paginated_chain_with_reset(fake_socket, initial_data):
    blockchain = initial_data[0]
    metadata = initial_data[1]

    thread = Thread(target=get_chain_paginated, args=(4, metadata, None, fake_socket), daemon=True)
    thread.start()

    run_once = True

    data = fake_socket.read_data()

    total_list = data['section']

    assert data['status'] == 'INITIAL'

    while True:
        if run_once:
            blockchain.increment_version_number()
            total_list = []
        fake_socket.set_data({"action": "inform", "params": {"message": "ACK"}})

        data = fake_socket.read_data()

        total_list = data['section'] + total_list

        if data['status'] == 'FINISHED':
            break

        if run_once:
            assert data['status'] == 'INITIAL'
            run_once = False
        else:
            assert data['status'] == 'CONTINUE'

    assert total_list == blockchain.get_chain()
    assert data['status'] == 'FINISHED'
