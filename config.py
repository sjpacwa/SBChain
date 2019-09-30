import configparser


class BlockchainConfig:
	def __init__(self):
		self.parser = configparser.ConfigParser()
		self.parser.read('config.ini')

	def get_block_difficulty(self):
		difficulty = self.parser.getint('General', 'difficulty')
		if difficulty < 0:
			return 0
		if difficulty > 256:
			return 256
		return difficulty
