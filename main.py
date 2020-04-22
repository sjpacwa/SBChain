"""
main.py

This file is responsible for parsing the command line arguments and 
starting the Flask webserver for the node.
"""

# Standard Library Imports
from argparse import ArgumentParser

#local imports
from macros import NEIGHBORS
from node import Node

if __name__ == '__main__':
    # Parse command line arguments.
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, 
        help='port to listen on')
    parser.add_argument('-ip', '--ip', default='localhost', type=str, 
        help='ip to listen on')
    parser.add_argument('-id', '--id', default=None, type=str, 
        help='id of node')
    parser.add_argument('--debug',default = False,action='store_true')    

    args = parser.parse_args()
    port = args.port
    ip = args.ip
    node_id = args.id
    debug = args.debug
   
    # Create the node.
    node = Node(ip, port, debug, NEIGHBORS, node_id)

