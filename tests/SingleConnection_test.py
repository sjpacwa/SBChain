"""
SingleConnection_test.py

This file tests the SingleConnectionHandler

2020 Stephen Pacwa and Daniel Okazaki
Santa Clara University
"""

# Local imports
from connection import SingleConnectionHandler

# Third party imports
import pytest


"""

Setup:
    Create a node with a known host and port

Test:
    Connect to a node that exist
        Send requests to connection
        Send requests that pass JSON parsing
        Send requests that don't pass JSON parsing
        Send requests where we expect a response
    Connect to a node that doesn't exist

Teardown:
    Nothing is needed

"""


class ThreadFailed(Exception):
    pass


@pytest.fixture(scope="module")
def node_a():
    from node import Node
    from threading import Thread, Semaphore

    initialized = Semaphore(0)

    thread = Thread(target=Node, args=('localhost', 5000, initialized), daemon=True)
    thread.start()

    while not initialized.acquire(blocking=False):
        if not thread.is_alive():
            raise ThreadFailed

    return None


def test_invalid_connection(node_a):
    with pytest.raises(ConnectionRefusedError):
        SingleConnectionHandler('localhost', 5001)


def test_valid_connection(node_a):
    SingleConnectionHandler('localhost', 5000)


def test_send_wout_response(node_a):
    conn = SingleConnectionHandler('localhost', 5000)
    conn.send_wout_response({"action": "wait_test", "params": [1, 1]})


def test_send_with_response_bad_2(node_a):
    conn = SingleConnectionHandler('localhost', 5000)
    data = conn.send_with_response({"action": "wait_test", "params": ["one"]})
    assert data == "Error: invalid data"


def test_send_with_response_bad(node_a):
    conn = SingleConnectionHandler('localhost', 5000)
    data = conn.send_with_response({"action": "wait_test", "args": [1]})
    assert data == "Error: Bad request"


def test_send_with_response_good(node_a):
    conn = SingleConnectionHandler('localhost', 5000)
    data = conn.send_with_response({"action": "response_test", "params": []})
    assert data == {"message": "hello"}
