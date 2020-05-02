import socket
import json

def MINE():
    return {
        'name':"mine"
    }

HOST = 'localhost'  # The server's hostname or IP address
PORT = 5000       # The port used by the server

data = ""
bufr_size = 1024

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    s.send(str(len(json.dumps(MINE()))).encode())
    ack = s.recv(16)
    s.send(json.dumps(MINE()).encode())

    s.close()