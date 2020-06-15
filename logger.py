"""
logger.py

This file is responsible for handling of the logging module

2020 Stephen Pacwa and Daniel Okazaki
Santa Clara University
"""

# Standard library imports
import logging
from os import mkdir


def initialize_log(node_id,debug):
    """
    initialize_log()

    Initializes the folder and the logs for the respective node.
    Initializes the file and console handlers

    :param node_id: <str> The node ID.
    :param debug: <bool> Determines the logging level. DEBUG if debug else INFO
    """
    try:
        mkdir("logs", 0o777)
    except OSError:
        pass

    logs_path = "logs/" + node_id + ".log"

    logger = logging.getLogger()

    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    # Create handlers
    f_handler = logging.FileHandler(logs_path)
    c_handler = logging.StreamHandler()

    log_format = logging.Formatter('%(asctime)s - %(funcName)s() - %(levelname)s - %(message)s')

    if debug:
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

