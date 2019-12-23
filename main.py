"""
main.py

This file is responsible for parsing the command line arguments and 
starting the Flask webserver for the node.
"""

# Standard Library Imports
from argparse import ArgumentParser
import logging
from threading import Thread

#local imports
from network import NetworkHandler
from multicast import MulticastHandler
from macros import NEIGHBORS
from mine import mine_loop

if __name__ == '__main__':
    # Parse command line arguments.
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, 
        help='port to listen on')
    parser.add_argument('-ip', '--ip', default='localhost', type=str, 
        help='ip to listen on')
    parser.add_argument('--debug',default = False,action='store_true')    
    args = parser.parse_args()
    port = args.port
    ip = args.ip

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    nh = NetworkHandler(ip, port)

    # TODO decide who gets to register nodes, might need a centralized source that returns a random set of nodes to be neighbors
    nh.register_nodes(NEIGHBORS)
    th = Thread(target=mine_loop, args=(nh,))
    th.start()
    nh.event_loop()


    
