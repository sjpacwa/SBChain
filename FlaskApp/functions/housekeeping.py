import random
from csv import reader
import os
import json

def check_port(ip, port_number):
    # checking for the validation of ip address
    try:
        ipaddress.ip_address(ip)
    except ValueError:
        return False

    # checking validation of the port_number
    try:
        port_number = int(port_number)
    except ValueError:
        return False

    if 1 <= port_number <= 65535:
        return True
    return False


def allowed_file(filename):
    if "." not in filename:
        return False

    extension = filename.rsplit(".", 1)[1]

    if extension.upper() in app.config["CSV"]:
        return True
    else:
        return False

def generate_network_information_csv_file(n, type):

    adjacency_matrix = generate_adjacency_matrix(n, type)
    create_csv_file(n, adjacency_matrix)

    #print(adjacency_matrix)

def generate_adjacency_matrix(n, type):
    adjacency_matrix = [[0 for i in range(n)]
                        for j in range(n)]

    if type == 'all':
        for row in range(n):
            for column in range(n):
                if row != column:
                    adjacency_matrix[row][column] = 1
    else:
        current_connections = [0 for i in range(n)]

        for row in range(n):
            for column in range(row + 1, n):
                if row != column and random.randint(0, 1) == 1:
                    adjacency_matrix[row][column] = adjacency_matrix[column][row] = 1
                    current_connections[row] += 1
                    current_connections[column] += 1

        for node in range(n):
            while current_connections[node] == 0:
                random_node = random.randint(0, n - 1)
                if random_node != node:
                    current_connections[node] += 1
                    current_connections[random_node] += 1
                    adjacency_matrix[node][random_node] = adjacency_matrix[random_node][node] = 1

    return adjacency_matrix

# TODO
def create_csv_file(n, adjacency_matrix):
    return

def read_network_information_file(file_path):
    adjacency_matrix = []
    with open(file_path, 'r') as file_object:
        flag = True
        csv_reader = reader(file_object)
        for row in csv_reader:
            if flag:
                n = int(row[0])
                flag = False
                continue
            adjacency_matrix.append(row)
    return n, adjacency_matrix

def create_nodes(n):
    nodes = []
    for i in range(n):
        stream = os.popen("kubectl create -f blockchain.yml")
        output = stream.read()
        node_name = output.split(" ")[0][4:]
        os.system("kubectl expose pod " + node_name + " --type=NodePort")
        nodes.append(node_name, get_port(node_name))
    return nodes


def get_port(service_name):
    stream = os.popen("kubectl get -o json service" + service_name)
    output = stream.read()
    return int(json.loads(output)["spec"]["ports"][0]["nodePort"])

def connect_neighbours(ports, adjacency_matrix):
    for i in range(len(ports)):
        ip = "127.0.0.1"
        port = ports[i]

        adjacency_list = []

        for j in range(len(ports)):
            if adjacency_matrix[i][j] == 1:
                adjacency_list.append(["127.0.0.1", ports[j]])

        # create connection to port
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

        information = {
                            "action": "register_nodes",
                            "params": adjacency_list
                        }

        json_information = json.dumps(information)
        data_size = len(json_information)

        try:
            # send length of the transaction first
            client_socket.send(str(data_size).encode())
            client_socket.recv(1024)

            # send neighbour information
            client_socket.send(json_information.encode())
        finally:
            print("Neighbours added for " + str(port))

def initialize_benchmark():
    return

