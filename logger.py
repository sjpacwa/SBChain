"""
logger.py
This file is responsible for handling of the logging module
"""

# Standard library imports
import logging
from os import mkdir


def initialize_log(node_id,debug):
    """
    initialize_log()

    Not Thread Safe

    Initializes the folder and the logs for the respective node.

    Initializes the file and console handlers

    :param node_id: <str> Node ID.
    :param debug: <bool> Determines the logging level. DEBUG if debug else INFO
    """
    try:
        mkdir("logs",0o777 )
    except OSError as error:
        pass
    except:
        raise

    logs_path = "logs/" + node_id +".log"

    logger = logging.getLogger()

    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.ERROR)
    # Create handlers
    f_handler = logging.FileHandler(logs_path)
    c_handler = logging.StreamHandler()

    log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

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
