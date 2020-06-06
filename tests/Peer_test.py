"""
Peer_test.py

This file tests the registering and unregistering of peers.
"""

from tasks import register_nodes, unregister_nodes
from tests.constants import create_metadata

import pytest


@pytest.fixture()
def initial_metadata():
    return create_metadata()


def test_adding_valid_peer(initial_metadata):
    valid_peer = [('127.0.0.1', 5001)]

    register_nodes(valid_peer, initial_metadata)

    assert initial_metadata['peers'] == valid_peer


def test_adding_multiple_valid_peers(initial_metadata):
    valid_peers = [('127.0.0.1', 5001), ('127.0.0.1', 5002)]

    register_nodes(valid_peers, initial_metadata)

    assert initial_metadata['peers'] == valid_peers


def test_adding_duplicate_peers(initial_metadata):
    duplicate_peers = [('127.0.0.1', 5001), ('127.0.0.1', 5001)]
    valid_peer = [('127.0.0.1', 5001)]

    register_nodes(duplicate_peers, initial_metadata)

    assert initial_metadata['peers'] == valid_peer


def test_adding_valid_netloc_peer(initial_metadata):
    valid_peer = [('localhost', 5001)]

    register_nodes(valid_peer, initial_metadata)

    assert initial_metadata['peers'] == valid_peer


def test_adding_invalid_peers(initial_metadata):
    invalid_peers = [('invalid', 'invalid'), (None, None), (5000, 5000), 'Non tuple address']

    register_nodes(invalid_peers, initial_metadata)

    assert initial_metadata['peers'] == []


def test_adding_valid_peer_with_invalid_peers(initial_metadata):
    peers = [('invalid', 'invalid'), (None, None), ('127.0.0.1', 5001), (5000, 5000), 'Non tuple address']
    valid_peer = [('127.0.0.1', 5001)]

    register_nodes(peers, initial_metadata)

    assert initial_metadata['peers'] == valid_peer


def test_adding_without_wrapped(initial_metadata):
    peer = ('127.0.0.1', 5001)

    register_nodes(peer, initial_metadata)

    assert initial_metadata['peers'] == []


def test_remove_present_peer(initial_metadata):
    present_peer = ('127.0.0.1', 5001)
    initial_metadata['peers'].append(present_peer)

    unregister_nodes([present_peer], initial_metadata)

    assert initial_metadata['peers'] == []


def test_remove_present_list_peer(initial_metadata):
    present_peer = ('127.0.0.1', 5001)
    initial_metadata['peers'].append(present_peer)

    unregister_nodes([list(present_peer)], initial_metadata)

    assert initial_metadata['peers'] == []


def test_remove_non_present_peer(initial_metadata):
    non_present_peer = ('127.0.0.1', 5001)
    present_peer = [('127.0.0.1', 5002)]
    initial_metadata['peers'] = present_peer

    unregister_nodes([non_present_peer], initial_metadata)

    assert initial_metadata['peers'] == present_peer


def test_remove_not_wrapped(initial_metadata):
    present_peer = ('127.0.0.1', 5001)
    initial_metadata['peers'].append(present_peer)

    unregister_nodes(present_peer, initial_metadata)

    assert initial_metadata['peers'] == [present_peer]

