"""
history.py

This class is implemented with a nested class in order to enforce the 
Singleton property. This should guarantee that only one instance of the 
inner __History class should exist on a node when the program is run.
"""

from copy import deepcopy
from threading import Lock

from wallet import Wallet


class History:
    """
    History
    """

    class __History:
        history_lock = Lock()
        
        def __init__(self, uuid):
            self.coins = {}
            self.transactions = {}

            self.uuid = uuid
            self.wallet = Wallet()

        def get_coin(self, uuid):
            return self.coins.get(uuid)

        def get_transactions(self):
            return self.transactions

        def get_transaction(self, uuid):
            return self.transactions.get(uuid)

        def add_coin(self, coin):
            self.coins[coin.get_uuid()] = coin

        def add_transaction(self, transaction):
            self.transactions[transaction.get_uuid()] = transaction

            our_new_coins = transaction.get_output_coins(self.uuid)
            if our_new_coins != None:
                for coin in our_new_coins:
                    self.wallet.add_coin(coin)
  
            if transaction.get_sender() == self.uuid:
                for coin in transaction.get_inputs():
                    self.wallet.remove_coin(coin.get_uuid())

        def remove_coin(self, uuid):
            try:
                del self.coins[uuid]
            except KeyError:
                pass

        def remove_transaction(self, uuid):
            transaction = self.transactions[uuid]

            if transaction.get_sender() == self.uuid:
                for coin in transaction.get_inputs():
                    self.wallet.add_coin(coin)

            our_bad_coins = transaction.get_output_coins(self.uuid)
            if our_bad_coins != None:
                for coin in our_bad_coins:
                    self.wallet.remove_coin(coin.get_uuid())

            try:
                del self.transactions[uuid]
            except KeyError:
                pass

        def get_lock(self):
            return self.history_lock

        def get_wallet(self):
            return self.wallet

        def reset(self):
            self.coins = {}
            self.transactions = {}

            self.wallet = Wallet()

    instance = None

    def __init__(self, uuid=""):
        """
        __init__()

        The constructor for the history object.

        :param uuid: <str> The UUID of the node.
        """

        if not History.instance:
            if uuid == "":
                raise ValueError("Initial history needs proper UUID")
            History.instance = History.__History(uuid)
    
    def get_coin(self, uuid):
        """
        get_coin()

        Retrieves the given coin.

        :param uuid: <str> The UUID of the coin.

        :return: <Coin Object> The coin if it exists or None.
        """

        return History.instance.get_coin(uuid)

    def get_transactions(self):
        """
        get_transaction()

        Retrieves all the transactions.

        :return: <list<Transaction Object>> The transactions stored in
            the history.
        """

        return History.instance.get_transactions()

    def get_transaction(self, uuid):
        """
        get_transaction()

        Retrieves the given transaction

        :param uuid: <str> The UUID of the transaction.

        :return <Transaction Object> The transaction if it exists
            or None.
        """

        return History.instance.get_transaction(uuid)

    def add_coin(self, coin):
        """
        add_coin()

        Adds a new coin to the history.

        :param coin: <Coin Object> The new coin to add.
        """

        History.instance.add_coin(coin)

    def add_transaction(self, transaction):
        """
        add_transaction()

        Adds a new transaction to the history. If the owner of the coin is 
            this node it also interfaces with the wallet to update it.

        :param transaction: <Transaction Object> The new 
            transaction to add.
        """

        History.instance.add_transaction(transaction)

    def remove_coin(self, uuid):
        """
        remove_coin()

        Removes a coin from the history.

        :param uuid: <str> The UUID of the coin.
        """

        History.instance.remove_coin(uuid)

    def remove_transaction(self, uuid):
        """
        remove_transaction()

        Removes a transaction from the history.

        :param uuid: <str> The UUID of the transaction.
        """

        History.instance.remove_transaction(uuid)

    def get_lock(self):
        """
        get_lock()

        Retrieves the lock that should be used when accessing the history.

        :return: <Lock> The lock object.
        """

        return History.instance.get_lock()

    def get_copy(self):
        """
        get_copy()

        Creates a deepcopy of the inner History instance so that it can
        be used for checks and temporary situations.

        :return: <History Object> The copy of the History.
        """

        return deepcopy(History.instance)

    def replace_history(self, history):
        """
        replace_history()

        Replaces the inner History instance with a new one.
        
        :param history: <History object> The object to replace the instance
            with.
        """

        History.instance = history

    def get_wallet(self):
        """
        get_wallet()

        Retrieves the wallet that is stored in the history.

        :return: <Wallet Object> The stored wallet.
        """

        return History.instance.get_wallet()

    def reset(self):
        """
        reset()

        Resets all of the parameters of the history.
        """

        History.instance.reset()

