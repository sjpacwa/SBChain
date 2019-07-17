"""
main.py
This file is responsible for starting the server for the node.
"""

# Standard library imports
from argparse import ArgumentParser
import logging
from logging.handlers import RotatingFileHandler


# Local imports
from api import app

if __name__ == '__main__':
	# Parse command line arguments.
	parser = ArgumentParser()
	parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
	args = parser.parse_args()
	port = args.port
	
	logHandler = RotatingFileHandler('info.log', maxBytes=1000, backupCount=1)	# Run the application.
	logHandler.setLevel(logging.INFO)
	app.logger.setLevel(logging.INFO)
	app.logger.addHandler(logHandler)    


	app.run(host='0.0.0.0', port=port)
