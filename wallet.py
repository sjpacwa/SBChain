"""
wallet.py

The wallet is responsible for converting currency amounts to internal 
coins to allow for ease of use of the blockchain.

2020 Stephen Pacwa and Daniel Okazaki
Santa Clara University
"""

from threading import Lock


class Wallet:
    """
    Wallet
    """

    # Static lock for the wallet
    wallet_lock = Lock()

    def __init__(self):
        """
        __init__()
    
        The constructor for a Wallet object.
        """
        self.personal_coins = []
        self.uuid_lookup = {}
        self.balance = 0

    def add_coin(self, coin):
        """
        add_coin()
    
        Adds a coin to the wallet 

        :param coin: <Coin Object> Coin to add to the wallet
        """
        self.personal_coins.append(coin)
        self.personal_coins.sort()
        self.uuid_lookup[coin.get_uuid()] = coin
        self.balance += coin.get_value()

    def remove_coin(self, uuid):
        """
        remove_coin()
    
        This function removes a coin from the wallet

        :param uuid: <str> UUID of the coin to remove from the wallet
        """
        try:
            coin = self.personal_coins.remove(self.uuid_lookup[uuid])
            del self.uuid_lookup[uuid]
            if coin != None:
                self.balance -= coin.get_value()
        except (ValueError, KeyError):
            pass

    def get_balance(self):
        """
        get_balance()
    
        This function returns the total balance of the wallet
        
        :return: <double> Balance in wallet
        """
        return self.balance

    def get_coins(self, value):
        """
        get_coins()
    
        Converts an input value into coins

        :param value: <double> Value of input coins

        :return: <tuple<list<Coin Object>, <double>> A tuple with the list of input coins and the value for the change
                 <boolean> Whetehr or not there was emnough coins in the wallet to complete the transaction
        """
        num_coins = 0
        coins = []

        for i in self.personal_coins[::-1]:
            value -= i.get_value()
            coins.append(i)
            num_coins += 1
            if value < 0:
                break
        else:
            return (), False

        for coin in coins:
            self.remove_coin(coin.get_uuid())

        return (coins, abs(value)), True

    def get_lock(self):
        """
        get_lock()
    
        This function returns the wallet lock
        
        :return: <Lock> Wallet Lock
        """
        return Wallet.wallet_lock

