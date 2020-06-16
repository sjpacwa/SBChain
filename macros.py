"""
macros.py

This file stores many functions that are used in many places to simplify
message creation and starting data.

2020 Stephen Pacwa and Daniel Okazaki
Santa Clara University
"""


BUFFER_SIZE = 256

REWARD_COIN_VALUE = 5


INITIAL_PEERS = [
    ('localhost', 5000),
    ('localhost', 5001)
]


def RECEIVE_BLOCK(block, host, port):
    """
    RECEIVE_BLOCK()

    This function creates a message for the receive block task.

    :param block: <Block Object> The block to send.
    :param host: <str> The node's host to facillitate callback.
    :param port: <int> The node's port to facillitate callback.

    :return: <str> The formatted message.
    """

    return {
        'action': 'receive_block',
        'params': [
            block,
            host,
            port
        ]
    }


def RECEIVE_TRANSACTION(transaction_list):
    """
    RECEIVE_TRANSACTION()

    This function creates a message for the receive transaction task.

    :param transaction_list: <list<Transaction Object>> A list of transactions
        to send.

    :return: <str> The formatted message.
    """

    return {
        'action': 'receive_transactions',
        'params': [transaction_list]
    }


def REGISTER_NODES(peer_list):
    """
    REGISTER_NODES()

    This function creates a message for the register nodes task.

    :param peer_list: <list<tuple<str, int>> A list of the peers to register.

    :return: <str> The formatted message.
    """

    return {
        'action': 'register_nodes',
        'params': [
            peer_list
        ]
    }


def RESOLVE_CONFLICTS(request_id, host, port, index):
    """
    RESOLVE_CONFLICTS()

    This function creates a message for the resolve conflicts task.

    :param request_id: <str> The request ID of this resolve conflicts
        request.
    :param host: <str> The host of the original requestor.
    :param port: <int> The port of the original requestor.
    :param index: <int> The current index being mined by the original
        requestor.

    :return: <str> The formatted message.
    """

    return {
        'action': 'resolve_conflicts_internal',
        'params': [
            request_id,
            host,
            port,
            index
        ]
    }


def GET_CHAIN_PAGINATED(size):
    """
    GET_CHAIN_PAGINATED()

    This function creates a message for the get chains paginated action.

    :param size: <int> The number of blocks to send per page.

    :return: <str> The formatted message.
    """

    return {
        'action': 'get_chain_paginated',
        'params': [
            size
        ]
    }


def GET_CHAIN_PAGINATED_ACK():
    """
    GET_CHAIN_PAGINATED_ACK()

    This function creates a message to acknowledge the get chain paginted task.

    :return: <str> The formatted message.
    """

    return {
        'action': 'inform',
        'params': {
            'message': 'ACK'
        }
    }


def GET_CHAIN_PAGINATED_STOP():
    """
    GET_CHAIN_PAGINATED_STOP()

    This function creates a message to stop the get chain paginated task.

    :return: <str> The formatted message.
    """

    return {
        'action': 'inform',
        'params': {
            'message': 'STOP'
        }
    }


def SEND_CHAIN(chain, length):
    """
    SEND_CHAIN()

    This function creates a message to reply to a get chain request.

    :param chain: <list<Block Object>> The chain to send.
    :param length: <int> The length of the sent chain.

    :return: <str> The formatted message.
    """

    return {
        'chain': chain,
        'length': length
    }


def SEND_CHAIN_SECTION(section, status):
    """
    SEND_CHAIN_SECTION()

    This function creates a message to reply to a get chain paginated
    request.

    :param section: <list<Block Object>> The subchain to send.'
    :param status: <str> The status of the reply message.

    :return: <str> The formatted message.
    """

    return {
        'section': section,
        'status': status
    }
