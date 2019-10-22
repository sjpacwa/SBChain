from math import ceil
from time import sleep
import json
import socket
import sys
import threading

BUFF_SIZE = 256


def sample(conn, arg):
	sleep(5)
	print('args: {}'.format(arg))

	if arg:
	    conn.sendall(arg.encode())
	else:
	    print('no data from', client)

	conn.close()


def network_event_loop(host, port):
	# Create a TCP/IP socket.
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	host = 'localhost'

	# Bind the socket to port.
	s.bind((host, port))

	while True:
		s.listen(5)

		print('waiting for connection.')
		connection, client = s.accept()

		# Get the size of the request data.
		data_size = int(connection.recv(16))

		# Determine number of buffers.
		num_buff = ceil(data_size / BUFF_SIZE)

		data = ''
		for i in range(num_buff):
			data += connection.recv(BUFF_SIZE).decode()

		json_data = json.loads(data[:data_size])

		function_name = json_data['name']
		function_args = json_data['args']

		print('Starting function {}. Arguments {}'.format(function_name, function_args))

		th = threading.Thread(target=sample, args=(connection, function_args,))
		th.start()

network_event_loop('localhost', 8080)