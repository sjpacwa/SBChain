import socket
import sys
import os
import random
from subprocess import Popen

available_port_numbers = []
total_number_nodes = 5
current_port_number = 5000

'''
# First get a list of n (=== number of nodes to be created) available port numbers on which we will run the nodes

number_nodes = total_number_nodes
while number_nodes != 0:
    print("Attempting socket connection: ")
    try:
        # create a socket to check for available port

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        connection = sock.connect_ex(('127.0.0.1', current_port_number))
        print("Status: " + str(connection))

        # if we are unable to connect with the socket at current port number then it is available and add it to the list of available port numbers. Also, reduce the additional number of port we need to look for.

        if connection == 10061:
            print("PORT: " + str(current_port_number) + " | Available.")
            available_port_numbers.append(current_port_number)
            number_nodes -= 1

        # error encountered: exiting the system

    except socket.error:
        print("Couldn't connect to the server.")
        sys.exit()

    current_port_number += 1

# run script to run deploy the block chain at these port numbers
for port_number in available_port_numbers:
    print("RUNNING SBCHAIN: port number " + str(port_number))
    Popen(["docker", "run", "-p", str(port_number)+":5000", "-t", "gurbirbasi/sb-chain"])
'''

# define a N x N matrix to represent the adjacency matrix

adjacency_matrix = [[0 for i in range(total_number_nodes)]
                    for j in range(total_number_nodes)]

# connect nodes either all together or raandomly
connect_all = False

if connect_all:
    for row in range(total_number_nodes):
        for column in range(total_number_nodes):
            if row != column:
                adjacency_matrix[row][column] = 1
else:
    '''
    current_connections = [0 for i in range(total_number_nodes)]
    for node in range(total_number_nodes):
        connections = random.randint(1, total_number_nodes - current_connections[node])
        print("NODE: " + str(node), end = '')
        print(" Connections: " + str(connections))
        while connections > 0:
            connection = random.randint(node + 1, total_number_nodes - 1)
            print("NODE: " + str(node), end = '')
            print("\tConnections Remaining: " + str(connections), end= "")
            print("\tConnection Attempt: " + str(connection) + "\t Value: " + str(adjacency_matrix[node][connection]))
            if adjacency_matrix[node][connection] != 1:
                print("Inside")
                adjacency_matrix[node][connection] = 1
                adjacency_matrix[connection][node] = 1
                current_connections[node]+= 1
                current_connections[connection] += 1
                connections -= 1
            else:
                continue
    '''
    current_connections = [0 for i in range(total_number_nodes)]
    for row in range(total_number_nodes):
        for column in range(row + 1, total_number_nodes):
            if row != column and random.randint(0,1) == 1:
                adjacency_matrix[row][column] = adjacency_matrix[column][row] = 1
                current_connections[row] += 1
                current_connections[column] += 1


    for node in range(total_number_nodes):
        while current_connections[node] == 0:
            random_node = random.randint(0, total_number_nodes - 1)
            if random_node != node:
                current_connections[node] += 1
                current_connections[random_node] += 1
                adjacency_matrix[node][random_node] = adjacency_matrix[random_node][node] = 1


    for number in range(total_number_nodes):
        register_neighbours(number, adjacency_matrix[number])

def register_neighbours(node_number, adjacency_list):

    ip = "127.0.0.1"
    port = available_port_numbers[node_number]

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

    neighbour_list = []

    for connection in range(total_number_nodes):
        if adjacency_list[connection] == 1:
            neighbour_list.append((ip, port))

    neighbour_information = {
            "name": "register_new_peers",
            "args": neighbour_list
    }

    json_neighbour_information = json.dumps(neighbour_information)
    data_size = len(json_neighbour_information)

    try:
        # send length of the transaction first
        client_socket.send(str(data_size).encode())
        client_socket.recv(1024)

        # send transaction
        client_socket.send(json_neighbour_information.encode())
    finally:
        print("Neighbours added sent.")