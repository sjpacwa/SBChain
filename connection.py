"""
connection.py

This file is responsible for storing the class that is responsible for 
socket-based network communication.
"""

# Standard library imports
from socket import socket, AF_INET, SOCK_STREAM
import json
import logging

# Local Imports
from macros import BUFFER_SIZE


class ConnectionHandler():
    def _send(self, conn, data):
        """
        _send()

        Not Thread Safe

        Send data to peer

        :param data: <str> Data to send JSON Object
        """

        try:
            json_data = json.dump(data)
            data_size = str(len(json_data))

            message = data_size + '~' + json_data

            conn.send(message.encode())
        except Exception as e:
            logging.warning('Error sending data to network: ' + str(e))

    def _recv(self, conn):
        """
        recv()

        Not Thread Safe

        This function will listen on the connection for the data.

        :param connection: <Socket Connection Object> The new connection.
        :param data_size: <int> The size of the incoming data.
        :param num_buffers: <int> The number of buffer cycles required.

        :return: <json> JSON representation of the data.
        """

        try:
            initial_message = conn.recv(BUFFER_SIZE).decode()
            print(initial_message)
            size, data = initial_message.split('~')

            size = int(size)
            amount_received = len(data)
            while amount_received < size:
                data += conn.recv(BUFFER_SIZE).decode()
                amount_received = len(data)

            return json.loads(data[:size])
        except OSError as e:
            # A timeout has occured.
            conn.close()
            return None
        except Exception as e:
            # All other exceptions
            logging.warning('Error receiving data from network: ' + str(e))


class SingleConnectionHandler(ConnectionHandler):
    def __init__(self, host, port):
        """
        __init__

        :raises ConnectionRefusedError: if the connection cannot be established.
        """
        ConnectionHandler.__init__(self)

        self.host = host
        self.port = port
        
        self.conn = socket(AF_INET, SOCK_STREAM)
        try:
            self.conn.connect((self.host, self.port))
        except ConnectionRefusedError as e:
            logging.warning("Error creating single connection " + str(e))
            raise e

    def send_with_response(self, data):
        """
        send_with_response()

        Not Thread Safe

        Send data and expect a response from peer

        :param data: <str> data to send.

        :return: <json> JSON representation of the data.
        """
        
        self._send(self.conn, data)
        received_data = self._recv(self.conn)
        self.conn.close()
        return received_data

    def send_wout_response(self, data):
        """
        send_wout_response()

        Not Thread Safe

        Send data and don't expect a response back

        :param data: <str> data to send.

        :return: <json> JSON representation of the data.
        """
        self._send(self.conn, data)
        self.conn.close()


class MultipleConnectionHandler(ConnectionHandler):
    def __init__(self, peers):
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
        peer_responses = []

        for conn in self.peer_connections:
            self._send(conn, data)
            received_data = self._recv(conn)
            self.conn.close()
            peer_responses.append(data)

        return peer_responses

    def send_wout_response(self, data):
        for conn in self.peer_connections:
            self._send(conn, data)
            self.conn.close()

