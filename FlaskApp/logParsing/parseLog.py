import "./transaction.py"
from datetime import datetime

# Transactions is a dictionary where a transaction object points to a list of string timestamps
transactions = {}

filePath = r"C:\Users\Gurbir\Desktop\Blockchain BenchMark\logging\SBChain\logs\184d97d771de4003af90fea0bb78b417.log";


with open(filePath, "r") as file:
    #we are reading each line individually using readline()
    line = file.readline()

    #looping till we reach end of the file
    while line:
        if line.__contains__("New Transaction"):
            #move the pointer to next line as it contains the information
            line = file.readline()

            #extract information from line
            start = line.find("{") + 1
            end = len(line) - 1

            transactionDetails = line[start:end].split(",")

            # create a transaction
            sender = transactionDetails[0].split(": ")[1]
            recipient = transactionDetails[1].split(": ")[1]
            amount = transactionDetails[2].split(": ")[1]
            transaction = Transaction(sender, recipient, amount)

            #get the timestamp
            timeStamp = transactionDetails[3].split(": ")[1]
            print(timeStamp)

            # add transaction as the key and the timestamp as the value to the dictionary transactions
            if transaction in transactions.keys():
                transactions[transaction] = transactions[transaction].append(timeStamp)
            else:
                transactions[transaction] = [timeStamp]

            transaction.print()
            print(str(transaction))
            print("TimeStamp: " + timeStamp)
        line = file.readline()


# sort each transaction in the dictionary by the timestamp

# '2020-03-20T22:59:37Z'

def sort_by_time_stamp(timestamp):
    return timestamp.sort(key=lambda date: datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ"))


def time_difference_seconds(time1, time2):
    return datetime.strptime(time1, "%Y-%m-%dT%H:%M:%SZ") - datetime.strptime(time1, "%Y-%m-%dT%H:%M:%SZ")


def find_threshold_point(timestamps, threshold):
    sort_by_time_stamp(timestamps)
    index = len(timestamps)*threshold
    return timestamps[index]


