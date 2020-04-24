from urllib.parse import urlparse
import logging

from multicast import MulticastHandler


def resolve_conflicts(blockchain, neighbors):
    """
    reslove_conflicts()

    Not Thread Safe

    Consensus algorithm at the node level

    :returns: <bool> True if our chain was replaced, else False
    """

    our_chain = blockchain.chain
    replace_chain = None
    chain = None

    # We're only looking for chains longer than ours
    our_length = len(our_chain)

    responses = MulticastHandler(neighbors).multicast_with_response(GET_CHAIN())
    logging.debug("Responses")
    logging.debug(responses)

    # Grab and verify the chains from all the nodes in our network
    for response in responses:
        if "Error" not in response:
            neighbor_length = response['length']
            neighbor_chain = response['chain']

            # Check if the neighbors chain is longer and if it is valid.
            if (neighbor_length > our_length 
                and blockchain.valid_chain(neighbor_chain)):
                our_length = neighbor_length
                chain = response['chain']
    if chain:
        logging.info("Replaced chain")
        logging.info(chain)
        # Replace our chain if we discovered a new, valid chain longer than ours
        replace_chain = []
        for block in chain:
            replace_chain.append(block_from_json(block))
        blockchain.chain = replace_chain
        return True
    return False


def register_nodes(peers, ip, port, nodes):
    """
    register_nodes()

    Add a new peer to the list of nodes

    NOTE: We assume that nodes don't drop later in the blockchain's lifespan


    :param address: <str> Address of peer. Eg. 'http://192.168.0.5:5000'
    :param port: <int> Port of peer.

    :raises: <ValueError> If the address is invalid
    """

    for peer in peers:
        logging.debug("Peer")
        logging.debug(peer)
        if peer[0] != ip or peer[1] != port:
            logging.debug("Registering Node")
            parsed_url = urlparse(peer[0])
            logging.debug("Parsed url")
            logging.debug(parsed_url)
            
            if parsed_url.netloc:
                nodes.append((parsed_url.netloc,peer[1]))
                logging.debug(parsed_url.netloc,peer[1])
            
            elif parsed_url.path:
                # Accepts an URL without scheme like '192.168.0.5:5000'.
                nodes.append((parsed_url.path,peer[1]))
                logging.debug(parsed_url.path,peer[1])
            
            else:
                logging.error('Invalid URL')
                logging.error(peer)
