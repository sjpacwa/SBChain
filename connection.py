"""
connection.py

This file is responsible for storing the class that is responsible for
socket-based network communication.

2020 Stephen Pacwa and Daniel Okazaki
Santa Clara University
"""

# Standard library imports
from socket import socket, AF_INET, SOCK_STREAM
import json
import logging

# Local Imports
from encoder import ComplexEncoder
from macros import BUFFER_SIZE


class ConnectionHandler():
    """
    ConnectionHandler
    """

    def _send(self, conn, data):
        """
        _send()

        Send data to peer

        :param conn: <Connection Object> The connection to use.
        :param data: <str> Data to send JSON Object
        """

        try:
            json_data = json.dumps(data, cls=ComplexEncoder)
            data_size = str(len(json_data))

            message = data_size + '~' + json_data

            conn.send(message.encode())
        except Exception as e:
            logging.warning('Error sending data to network: ' + str(e))

    def _recv(self, conn):
        """
        recv()

        This function will listen on the connection for the data.

        :param conn: <Connection Object> The connection to use.

        :return: <dict> JSON Object representation of the data.
        """

        try:
            initial_message = conn.recv(BUFFER_SIZE).decode()
            size, data = initial_message.split('~')

            size = int(size)
            amount_received = len(data)
            while amount_received < size:
                data += conn.recv(BUFFER_SIZE).decode()
                amount_received = len(data)

            json_data = json.loads(data[:size])
            return json_data
        except OSError as e:
            # A timeout has occured.
            logging.warning('Error receiving data from network: ' + str(e))
            conn.close()
            return None
        except Exception as e:
            # All other exceptions
            logging.warning('Error receiving data from network: ' + str(e))
            return None


class SingleConnectionHandler(ConnectionHandler):
    """
    SingleConnectionHandler
    """

    def __init__(self, host, port, close=True):
        """
        __init__()

        :param host: <str> The host to connect to.
        :param port: <int> The port to connect to.
        :param close: <boolean> Whether or not the connection should stay open
            after making a request.

        :raises ConnectionRefusedError: if the connection cannot be established.
        """

        ConnectionHandler.__init__(self)

        self.host = host
        self.port = port

        self.close = close

        self.conn = socket(AF_INET, SOCK_STREAM)
        try:
            self.conn.connect((self.host, self.port))
        except ConnectionRefusedError as e:
            logging.warning("Error creating single connection " + str(e))
            raise e

    def send_with_response(self, data):
        """
        send_with_response()

        Send data and expect a response from peer

        :param data: <str> data to send.

        :return: <dict> JSON Object representation of the data.
        """

        self._send(self.conn, data)
        received_data = self._recv(self.conn)
        if self.close:
            self.conn.close()
        return received_data

    def send_wout_response(self, data):
        """
        send_wout_response()

        Send data and don't expect a response back

        :param data: <str> data to send.
        """
        self._send(self.conn, data)
        if self.close:
            self.conn.close()


class MultipleConnectionHandler(ConnectionHandler):
    """
    MultipleConnectionHandler
    """

    def __init__(self, peers):
        """
        __init__()

        The constructor for the MultipleConnectionHandler object.

        :param peers: <list<tuple<str, int>>> A list of the peers that
            should be connected to.
        """

        ConnectionHandler.__init__(self)

        self.peers = peers
        self.peer_connections = []
        for peer in self.peers:
            conn = socket(AF_INET, SOCK_STREAM)
            try:
                conn.connect((peer[0], peer[1]))
                self.peer_connections.append(conn)
            except ConnectionRefusedError as e:
                logging.warning('Error creating a connection in multiple connection handler: ' + str(e))

    def send_with_response(self, data):
        """
        send_with_response()

        Send data and expect a response from peer

        :param data: <str> data to send.

        :return: <list<dict>> A list of the JSON Object representation of the data
            that was received from each node.
        """

        peer_responses = []

        for conn in self.peer_connections:
            self._send(conn, data)
            received_data = self._recv(conn)
            conn.close()
            peer_responses.append(received_data)

        return peer_responses

    def send_wout_response(self, data):
        """
        send_wout_response()

        Send data and don't expect a response back

        :param data: <str> data to send.
        """

        for conn in self.peer_connections:
            self._send(conn, data)
            conn.close()
