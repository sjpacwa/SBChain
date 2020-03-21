
# SBChain Blockchain

The code for this project was imported from the article [Building a Blockchain](https://medium.com/p/117428612f46). The original source code can be found [here](https://github.com/dvf/blockchain).

## Python

### Initial Setup

1. Make sure [Python 3.6+](https://www.python.org/downloads/) is installed. This can be tested by running `$ python -V`.

2. Ensure that pip runs properly by running `$ pip -V`. If this command doesn't work, try `$ python -m pip -V`.

4. Install [virtualenv](https://virtualenv.pypa.io/en/stable/installation/).
```
$ pip install virtualenv 
```

5. Create a new virtual environment for the project. The venv folder is included in the .gitignore file, so it is safe to create in the project directory.
```
$ virtualenv -p python venv
```

6. Mount the virtual environment. After this line, your command prompt should be prefaced with ```(venv)```.
```
$ .\venv\Scripts\activate
```

8. Run the server:
    * `$ python main.py` 
    * `$ python main.py -p 5001`
    * `$ python main.py --port 5002`

### Running after initial setup

1. Mount the virtual environment.
```
$ .\venv\Scripts\activate
```

2. Run the server:
    * `$ python main.py` 
    * `$ python main.py -p 5001`
    * `$ python main.py --port 5002`

### Configuring multiple nodes
1. Mount the virtual environment.
```
$ .\venv\Scripts\activate
```

2. Run several instances of the server with different port numbers.
```
$ python main -p 5000
$ python main -p 5001
$ python main -p 5002
```

NOTE: the current main.py is currently a skeleton for a fully operational node. Please make your own main.py file to better suit your needs.

## API

The following public API calls can be used to interact with the nodes in the blockchain. Ensure that the port number matches the port that the node is running on. Note that a socket connection must be established to send commands. The following commands specify the data format that is accepted by the dispatcher on the Blockchain node. 

To execute any of these commands.
1. Initiate a connection wit hthe node
2. Send the total length fo the JSON string that you want to send
3. Recieve an ACK from the node
4. Send the JSON string

NOTE: The following JSON can be in any acceptable JSON format, this specific format is to make it easier to read.

### new_transaction

Creates a new transaction at a node at the current block.
```
{
    name: new_transaction,
    args: {
            sender: "sender",
            recipient: "recipient",
            amount: "amount"
    }
}
```

### register_new_peers

Registers peers with node through dispatcher thread
```
{
    name: register_new_peers,
    args: [
            (ip1,port1),
            (ip2,port2)
    ]
}
```

### get_chain

Return the full blockchain
```
{
    name: get_chain
}
```

### get_block

Returns the current block of the given node
```
{
    name: get_block
}
```