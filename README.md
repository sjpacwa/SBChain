
# SBChain Blockchain

The code for this project was imported from the article [Building a Blockchain](https://medium.com/p/117428612f46). The original source code can be found [here](https://github.com/dvf/blockchain).

## Python

1. Make sure [Python 3.6+](https://www.python.org/downloads/) is installed. This can be tested by running `$ python -V`.

2. Install [virtualenv](https://virtualenv.pypa.io/en/stable/installation/).
```
$ pip install virtualenv 
```

4. Create a new virtual environment for this project. The venv folder will be ignored by GitHub.
```
$ virtualenv -p python3 venv
```

5. Mount the virtual environment. After this line, your command prompt should be prefaced with ```(venv)```.
```
$ .\local\venv\Scripts\activate
```

6. Install requirements.
```
$ pip install -r requirements.txt
``` 

7. Run the server:
    * `$ python blockchain.py` 
    * `$ python blockchain.py -p 5001`
    * `$ python blockchain.py --port 5002`
    
## Docker

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
