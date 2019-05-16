"""
main.py
This file is responsible for starting the server for the node.
"""
from argparse import ArgumentParser

from api import app

if __name__ == '__main__':
    

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    app.run(host='0.0.0.0', port=port)
