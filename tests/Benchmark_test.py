"""
Benchmark_test.py

This file tests the initialize functionality of the benchmark.
"""

from threading import Semaphore

from blockchain import Blockchain
from tasks import benchmark_initialize
from tests.constants import create_metadata

import pytest


@pytest.fixture()
def initial_metadata():
    metadata = create_metadata(blockchain=Blockchain())
    metadata['benchmark'] = True
    metadata['benchmark_lock'] = Semaphore(0)
    metadata['history'].reset()

    return metadata


@pytest.fixture()
def node_list():
    nodes = []
    for i in range(20):
        nodes.append('node_address_' + str(i))

    return nodes


def test_valid_initialize(initial_metadata, node_list):
    benchmark_initialize(node_list, 5, initial_metadata)

    # Check the flags are set.
    assert initial_metadata['benchmark'] == False
    assert initial_metadata['benchmark_lock']._value == 1

    assert len(initial_metadata['history'].instance.coins.values()) == len(node_list)
    assert len(initial_metadata['history'].instance.transactions.values()) == 1

    assert len(initial_metadata['blockchain'].chain[0].transactions) == 1


def test_benchmark_runs_once(initial_metadata, node_list):
    response_one = benchmark_initialize(node_list, 5, initial_metadata)

    response_two = benchmark_initialize(node_list, 5, initial_metadata)

    # Ensure second run is failure
    assert response_one == True
    assert response_two == False

    # Check the flags are set.
    assert initial_metadata['benchmark'] == False
    assert initial_metadata['benchmark_lock']._value == 1

    assert len(initial_metadata['history'].instance.coins.values()) == len(node_list)
    assert len(initial_metadata['history'].instance.transactions.values()) == 1

    assert len(initial_metadata['blockchain'].chain[0].transactions) == 1

