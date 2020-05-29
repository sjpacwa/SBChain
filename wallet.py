"""
wallet.py

The wallet is responsible for converting currency amounts to internal 
coins to allow for ease of use of the blockchain.
"""

from threading import Lock


class Wallet:
    wallet_lock = Lock()

    def __init__(self):
        self.personal_coins = []
        self.uuid_lookup = {}
        self.balance = 0

    def add_coin(self, coin):
        self.personal_coins.append(coin)
        self.personal_coins.sort()
        self.uuid_lookup[coin.get_uuid()] = coin
        self.balance += coin.get_value()

    def remove_coin(self, uuid):
        try:
            coin = self.personal_coins.remove(self.uuid_lookup[uuid])
            del self.uuid_lookup[uuid]
            self.balance -= coin.get_value()
        except ValueError:
            pass

    def get_balance(self):
        return self.balance

    def get_coins(self, value):
        num_coins = 0
        coins = []

        for i in self.personal_coins[::-1]:
            if value < 0:
                break
            value -= i.get_value()
            coins.append(i)
            num_coins += 1
        else:
            return (), False

        for coin in coins:
            self.remove_coin(coin.get_uuid())

        return (coins, abs(value)), True

    def get_lock(self):
        return wallet_lock

