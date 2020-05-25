"""
history.py

This class is implemented with a nested class in order to enforce the 
Singleton property. This should guarantee that only one instance of the 
inner __History class should exist on a node when the program is run.
"""

from threading import Lock


class History:
    class __History:
        history_lock = Lock()

        def __init__(self):
            self.coins = {}
            self.transactions = {}

        def get_coin(self, uuid):
            return self.coins.get(uuid)

        def get_transaction(self, uuid):
            return self.transactions.get(uuid)

        def add_coin(self, coin):
            self.coins[coin.get_uuid()] = coin

        def add_transaction(self, transaction):
            self.transactions[transaction.get_uuid()] = transaction

        def remove_coin(self, uuid):
            del self.coins[uuid]

        def remove_transaction(self, uuid):
            del self.transactions[uuid]

        def get_lock(self):
            return self.history_lock

    instance = None
    def __init__(self):
        if not History.instance:
            History.instance = History.__History()
    
    def get_coin(self, uuid):
        return History.instance.get_coin(uuid)

    def get_transaction(self, uuid):
        return History.instance.get_transaction(uuid)

    def add_coin(self, coin):
        History.instance.add_coin(coin)

    def add_transaction(self, transaction):
        History.instance.add_transaction(transaction)

    def remove_coin(self, uuid):
        History.instance.remove_coin(uuid)

    def remove_transaction(self, uuid):
        History.instance.remove_transaction(uuid)

    def get_lock(self):
        return History.instance.get_lock()

    def get_copy(self):
        return deepcopy(History.instance)

    def replace_history(self, history):
        History.instance = history

