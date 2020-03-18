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
    args = parser.parse_args()
    port = args.port
    ip = args.ip
    node_id = args.id
    debug = None

    try:
        mkdir("logs")
    except OSError:
        pass
    except:
        raise
    logs_path = "logs/" + node_id +".log"

    logger = logging.getLogger()
    # Create handlers
    f_handler = logging.FileHandler(logs_path)
    c_handler = logging.StreamHandler()

    log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    if args.debug:
        debug = True
        f_handler.setLevel(logging.DEBUG)
        c_handler.setLevel(logging.DEBUG)
    else:
        debug = False
        f_handler.setLevel(logging.INFO)
        c_handler.setLevel(logging.INFO)

    c_handler.setFormatter(log_format)
    logger.addHandler(c_handler)
    
    f_handler.setFormatter(log_format)
    logger.addHandler(f_handler)
   

    # Create location to keep track of received block.
    received_block = (Lock(), False, None)

    # Create the node.
    node = Node(node_id)

    # Create the network handler.
    nh = NetworkHandler(ip, port, node, debug)

    # Start the mining thread.
    th = Thread(target=mine_loop, args=(nh, received_block))
    th.start()

    # Automatically register neighbors.
    # TODO Remove this.
    nh.register_nodes(NEIGHBORS)

    # Start the network handler
    nh.event_loop()

