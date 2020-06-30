class Transaction:

    def __init__(self, sender, recipient, amount):
        self.sender = sender
        self.recipient = recipient
        self.amount = amount
        #self.timestamp = timestamp

    def print(self):
        print("Sender: " + self.sender + "\tRecipient: " + self.recipient + "\tAmount: " + self.amount)

    def __hash__(self):
        return hash(str(self.sender) + str(self.recipient) + str(self.amount))

    def __eq__(self, other):
        return self.sender == other.sender and self.recipient == other.recipient and self.amount == other.amount