from json import loads
from queue import Empty
import socket

from blockchain import Blockchain
from tests.constants import *
from tasks import receive_block

import pytest


@pytest.fixture(scope="module")
def blockchain():
    blockchain = Blockchain()

    blockchain.new_block("1", "1")
    blockchain.new_block("2", "2")

    return blockchain



def test_block_with_lower_index(blockchain):
    metadata = create_metadata(blockchain=blockchain)

    block = loads(BLANK_BLOCK(1, [], "1", "1"))

    receive_block(block, metadata, queues, FakeConnection())

    with pytest.raises(Empty):
        queues['blocks'].get(block=False)

def test_block_with_equal_index(blockchain):
    metadata = create_metadata(blockchain=blockchain)

    block = loads(BLANK_BLOCK(3, [], "3", "3"))

    receive_block(block, metadata, queues, FakeConnection())

    assert queues['blocks'].get(block=False) != None
    with pytest.raises(Empty):
        queues['blocks'].get(block=False)

def test_block_with_greater_index(blockchain):
    metadata = create_metadata(blockchain=blockchain)

    block = loads(BLANK_BLOCK(10, [], "10", "10"))

    receive_block(block, metadata, queues, FakeConnection())

    assert queues['blocks'].get(block=False) != None
    with pytest.raises(Empty):
        queues['blocks'].get(block=False)

