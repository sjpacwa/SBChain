"""
main.py

This file is responsible for parsing the command line arguments and 
starting the Flask webserver for the node.
"""

# Standard Library Imports
from argparse import ArgumentParser
import logging
from threading import Thread, Lock
from os import mkdir

#local imports
from network import NetworkHandler
from multicast import MulticastHandler
from macros import NEIGHBORS
from mine import mine_loop
from node import Node
from uuid import uuid4
from logger import initialize_log

if __name__ == '__main__':
    # Parse command line arguments.
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, 
        help='port to listen on')
    parser.add_argument('-ip', '--ip', default='localhost', type=str, 
        help='ip to listen on')
    parser.add_argument('-id', '--id', default=str(uuid4()).replace('-', ''), type=str, 
        help='id of node')
    parser.add_argument('--debug',default = False,action='store_true')    
    parser.add_argument('--test',default = False,action='store_true')    

    args = parser.parse_args()
    port = args.port
    ip = args.ip
    node_id = args.id
    debug = None
   
    initialize_log(node_id,args.debug)
    # Create location to keep track of received block.
    received_block = (Lock(), False, None)

    # Create the node.
    node = Node(node_id)

    # Create the network handler.
    nh = NetworkHandler(ip, port, node)

    if not args.test:
        # Start the mining thread.
        th = Thread(target=mine_loop, args=(nh, received_block))
        th.start()

    # Automatically register neighbors.
    # TODO Remove this.
    nh.register_nodes(NEIGHBORS)

    # Start the network handler
    nh.event_loop()

