import configparser


class BlockchainConfig:
	def __init__(self):
		"""
        __init__
        
        The constructor for a BlockChain Config object

        """
		self.parser = configparser.ConfigParser()
		self.parser.read('config.ini')

	def get_block_difficulty(self):
		"""
        get_block_difficulty()

        Not Thread Safe

		Returns the difficulty used for the blockchain

        :returns: <int> difficulty used in mining
        """
		difficulty = self.parser.getint('General', 'difficulty')
		if difficulty < 0:
			return 0
		if difficulty > 256:
			return 256
		return difficulty