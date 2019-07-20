"""
main.py

This file is responsible for parsing the command line arguments and 
starting the Flask webserver for the node.
"""

# Standard Library Imports
from argparse import ArgumentParser
from os import environ

# Local Imports
from api import app

if __name__ == '__main__':
	# Parse command line arguments.
	parser = ArgumentParser()
	parser.add_argument('-p', '--port', default=5000, type=int, 
		help='port to listen on')
	args = parser.parse_args()
	port = args.port

	# Add the port to the environment variables so the node knows what 
	# port it is at.
	environ['FLASK_PORT'] = str(port)

	# Run the app on localhost.
	app.run(host='0.0.0.0', port=port)
