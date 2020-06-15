"""
main.py

This file is responsible for parsing the command line arguments and 
starting the Flask webserver for the node.
"""

# Standard library imports
from argparse import ArgumentParser

# Local imports
from macros import INITIAL_PEERS
from node import Node


if __name__ == '__main__':
    # Parse command line arguments.
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, 
        help='port to listen on')
    parser.add_argument('-o', '--host', default='localhost', type=str, 
        help='ip to listen on')
    parser.add_argument('-i', '--id', default=None, type=str, 
        help='id of node')
    parser.add_argument('-b', '--benchmark', default=False, 
        action='store_true', help='initialize node for benchmark use')
    parser.add_argument('--debug', default=False, action='store_true')    
    parser.add_argument('--no_mine', default=False, action='store_true')

    args = parser.parse_args()
    port = args.port
    host = args.host
    uuid = args.id
    benchmark = args.benchmark
    debug = args.debug
    no_mine = args.no_mine
   
    # Create the node.
    node = Node(host, port, None, uuid, debug, no_mine, benchmark, INITIAL_PEERS)

