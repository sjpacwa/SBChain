import logging
from os import mkdir

def initialize_log(node_id,debug):
    try:
        mkdir("logs",0o777 )
    except OSError as error:
        print(error)
    except:
        raise

    logs_path = "logs/" + node_id +".log"

    if debug:
        logging.basicConfig(level = logging.DEBUG)
    else:
        logging.basicConfig(level = logging.INFO)

    logger = logging.getLogger()
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
