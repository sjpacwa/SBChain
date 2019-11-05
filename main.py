"""
main.py

This file is responsible for parsing the command line arguments and 
starting the Flask webserver for the node.
"""

# Standard Library Imports
from argparse import ArgumentParser
import logging
from network import NetworkHandler

# Local Imports
from api import app

if __name__ == '__main__':
	# Parse command line arguments.
	parser = ArgumentParser()
	parser.add_argument('-p', '--port', default=5000, type=int, 
		help='port to listen on')
	parser.add_argument('-ip', '--ip', default='localhost', type=str, 
		help='ip to listen on')
	args = parser.parse_args()
	port = args.port
	ip = args.ip

	logging.basicConfig(level=logging.INFO)


	nh = NetworkHandler(ip, port, {})
	nh.event_loop()

	
