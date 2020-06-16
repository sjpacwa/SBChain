"""
blockchainConfig.py

This file retrieves the Blockchain configuration

2020 Stephen Pacwa and Daniel Okazaki
Santa Clara University
"""

# Standard library imports
import configparser

class BlockchainConfig:
    """
    Blockchain Config
    """

    def __init__(self):
        """
        __init__()

        The constructor for a BlockChain Config object
        """

        self.parser = configparser.ConfigParser()
        self.parser.read('config.ini')


    def get_block_difficulty(self):
        """
        get_block_difficulty()

        Returns the difficulty used for the blockchain

        :returns: <int> difficulty used in mining
        """

        difficulty = self.parser.getint('General', 'difficulty')
        if difficulty < 0:
            return 0
        if difficulty > 256:
            return 256
        return difficulty
