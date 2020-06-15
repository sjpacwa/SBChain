from datetime import datetime
from json import loads
from queue import Empty
import socket

from block import block_from_string
from blockchain import Blockchain
from tests.constants import *
from tasks import receive_block
from mine import handle_blocks, proof_of_work, BlockException

import pytest


@pytest.fixture(scope="module")
def blockchain():
    blockchain = Blockchain()

    blockchain.new_block("1", "1", datetime.min.strftime('%Y-%m-%dT%H:%M:%SZ'))
    blockchain.new_block("2", "2", datetime.min.strftime('%Y-%m-%dT%H:%M:%SZ'))

    return blockchain



def test_block_with_lower_index(blockchain):
    metadata = create_metadata(blockchain=blockchain)

    block = loads(BLANK_BLOCK(1, [], "1", "1"))

    receive_block(block, '127.0.0.1', 5000, metadata, queues, FakeConnection())

    with pytest.raises(Empty):
        queues['blocks'].get(block=False)

def test_block_with_equal_index(blockchain):
    metadata = create_metadata(blockchain=blockchain)

    block = loads(BLANK_BLOCK(4, [], "3", "3"))

    receive_block(block, '127.0.0.1', 5000, metadata, queues, FakeConnection())

    assert queues['blocks'].get(block=False) != None
    with pytest.raises(Empty):
        queues['blocks'].get(block=False)


def test_block_with_good_transaction(blockchain):
    metadata = create_metadata(blockchain=blockchain)
    
    block = block_from_string(BLANK_BLOCK(4, [Transaction("B", [Coin("ABC", 100, "TEST")],{"C": [Coin("DCE", 100, "OUTCOIN")]}, "DCE", datetime.min.strftime('%Y-%m-%dT%H:%M:%SZ'))], 25399, "7b351d6c1a892f09469c7a44932de17b94e9fe44f94acc68f87077c2780c1f87"))

    queues['blocks'].put((('127.0.0.1', 5000), block))

    with pytest.raises(BlockException):
        handle_blocks(metadata, queues)

    assert queues['tasks'].get(block=False) != None
    with pytest.raises(Empty):
        queues['tasks'].get(block=False)


def test_block_with_bad_transaction(blockchain):
    metadata = create_metadata(blockchain=blockchain)
    
    block = block_from_string(BLANK_BLOCK(4, [Transaction("B", [Coin("XYZ", 100, "TEST")],{"C": [Coin("DCE", 100)]}, "DCE")], "3", "3"))

    queues['blocks'].put((('127.0.0.1', 5000), block))

    handle_blocks(metadata, queues)

    with pytest.raises(Empty):
        queues['tasks'].get(block=False)


def test_block_with_greater_index(blockchain):
    metadata = create_metadata(blockchain=blockchain)

    block = loads(BLANK_BLOCK(10, [], "10", "10"))

    receive_block(block, '127.0.0.1', 5000, metadata, queues, FakeConnection())

    assert queues['blocks'].get(block=False) != None
    with pytest.raises(Empty):
        queues['blocks'].get(block=False)

