def check_transaction(sender, recipient, amount):
    # TODO: check for sender and recipient
    return int(amount) > 0
def send_single_transaction(transaction, node):
    # node details
    ip = node[0]
    port = int(node[1])

    # transaction details
    sender = transaction[0]
    recipient = transaction[1]
    amount = int(transaction[2])

    # create socket connection
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print("Socket created.")
    except socket.error as err:
        print("Error Creating Socket: ERROR: " + err)
    try:
        client_socket.connect((ip, port))
        print("Successful connection to node: ")
    except ConnectionError:
        print("Error: ")
        print(ConnectionError)
        return
    except ConnectionRefusedError:
        print("Error: ")
        print(ConnectionRefusedError)
        return

    transaction_information = {
            "name": "new_transaction",
            "args": {
                "sender": sender,
                "recipient": recipient,
                "amount": amount
            }
    }
    json_transaction_information = json.dumps(transaction_information)
    data_size = len(json_transaction_information)

    try:
        # send length of the transaction first
        client_socket.send(str(data_size).encode())
        client_socket.recv(1024)

        # send transaction
        client_socket.send(json_transaction_information.encode())
    finally:
        print("Transaction sent.")
