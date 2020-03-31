import socket
import json

def GET_BLOCK(index):
    return {
        'name':"get_block",
        'args': str(index)
    }

HOST = 'localhost'  # The server's hostname or IP address
PORT = 5000       # The port used by the server

data = ""
bufr_size = 1024

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    s.send(str(len(json.dumps(GET_BLOCK(0)))).encode())
    ack = s.recv(16)
    s.send(json.dumps(GET_BLOCK(0)).encode())

    size = int(s.recv(16).decode())
    s.send('ACK'.encode())

    num_bufs = int(size/bufr_size) + 1

    for i in range(num_bufs):
        d = s.recv(1024).decode()
        data += d

    print('Received:', data)
    s.close()