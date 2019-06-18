
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

7. Install the project requirements.
```
$ pip install -r requirements.txt
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

3. Register the nodes with each other through the `/nodes/register` API call. This must be done from both ends, so node:5000 must be registered with node:5001 and node:5001 must be registered with node:5000.

## Docker (untested in current version)

Another option for running this blockchain program is to use Docker.  Follow the instructions below to create a local Docker container:

1. Clone this repository

2. Build the docker container
```
$ docker build -t blockchain .
```

3. Run the container
```
$ docker run --rm -p 80:5000 blockchain
```

4. To add more instances, vary the public port number before the colon:
```
$ docker run --rm -p 81:5000 blockchain
$ docker run --rm -p 82:5000 blockchain
$ docker run --rm -p 83:5000 blockchain
```

## API

The following API calls can be used to interact with the nodes in the blockchain. Ensure that the port number matches the port that the node is running on. 

If you are running the nodes on a Unix machine, the following curl commands should work. If you are using Windows, consider using [Postman](https://www.getpostman.com/) to organize your API calls.

### GET /mine

Tell the node to mine a new block.
```
$ curl -X GET "http://localhost:5000/mine"
```

### GET /chain

Return the full blockchain
```
$ curl -X GET "http://localhost:5000/chain"
```

### POST /transactions/new

Create a new transaction in the current block.
```
$ curl -X POST -H "Content-Type: application/json" -d '{  
 "sender": "your-address",  
 "recipient": "someone-other-address",  
 "amount": 5  
}' "http://localhost:5000/transactions/new"
```

### POST /nodes/register

Add a new node to the list of peers for this node.
```
$ curl -X POST -H "Content-Type: application/json" -d '{
 "nodes": ["127.0.0.1"]
}' "https://localhost:5000/transactions/new"
```

### GET /nodes/resolve

Resolve conflicts and keep the chain that is longer.
```
$ curl -X GET "http://localhost:5000/nodes/resolve"
```
