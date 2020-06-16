
# SBChain Blockchain

The SBChain Blockchain project meant to explore possible performance improvements to the Bitcoin implementation of Blockchain without needing to modify the Bitcoin source code. This project provides an easy interface for platforms of various codebases to be able to interact with the Blockchain using a socket interface. This project implements all of the core functionalities of Bitcoin to make it functional. This project is meant to be used as a base model for performance metrics against different implementations of Blockchain based on this codebase.


## First Time Setup

1. Ensure that Python 3 is installed. This can be checked by running: 
   ```
   python3 -v
   ```
2. Clone the repository to the local machine and navigate to the root directory.
3. Create a virtual environment by running: 
   ```
   python -m venv venv
   ```
    This will create a virtual environment in the venv subdirectories and helps manage dependencies associated with the project.
4. Mount the virtual environment by running: 
   ```
   source venv/bin/activate
   ```
5. Install the dependencies that are needed by running 
   ```
   pip install -r requirements.txt
   ```
    Note that these dependencies are only necessary for running the testing suite.


## Running

1. Mount the virtual environment.
    ```
    $ .\venv\Scripts\activate
    ```

2. Run the server:

    Run the following command:   
    ```
    python main.py [-p <port>] [-o <host>] [-i <id>] [-b] [--debug]
    ```

    A description of the arguments follows: 
    * -p	--port
        - The port to bind the node to. Default is 5000.
    * -o	--host
        - The host to bind the node to. Default is localhost.
    * -i	--id
        - The ID to assign to the node. Default is randomly generated.
    * -b	--benchmark	
        - Configures the node for a special benchmark initialization. This will allow each node in the network to be assigned a starting amount of money that can then be pulled from during a benchmark run. See API reference for Benchmark Initialize for more information.
 	* --debug
        - Start the node in debug mode which prints more information.
 	* --no-mine		
        - Start the node without allowing it to mine new blocks.

## Configuring multiple nodes
1. Open a new terminal
2. Mount the virtual environment.
    ```
    $ .\venv\Scripts\activate
    ```

3. Run new instance of the server with a different port numbers.
    ```
    $ python main.py -p 5003
    ```



## API

The following public API calls can be used to interact with the nodes in the blockchain. Ensure that the port number matches the port that the node is running on. Note that a socket connection must be established to send commands. The following commands specify the data format that is accepted by the dispatcher on the Blockchain node. All commands have the parameter "action" which specifies which API method to call


To execute any of these commands.
1. Initiate a socket connection with the node
2. Send the total length of the JSON string that you want to send appended by '~' followed by the command
    * Example: 37~{"action": "get_chain", "params": [ ] }

## **new_transaction**

**Description**:  
Creates a new transaction at a node at the current block. 

**Parameters**:
1. "input": the amount of money to be used as an input
2. "output": Dictionary of all recipients of this transactions as well as the amount to give each recipient

**Assumptions**:
1. The node that receives this endpoint call is the sender
2. (input - total output value) is given to the miner as a reward. 

The input amount is automatically converted to coins using the internal wallet interface, and if needed, change is automatically given back to the sender.

```
{
    "action": "new_transaction",
    "params": [
        {
            "input": <amount>,
            "output": {
                "recipient1": <amount>,
                "recipient2": <amount>,
                ... 
            }
        }
    ]
}
```

## **register_nodes**

**Description**:  
Registers peers with node through dispatcher thread. The node who receives this call will automatically forward this request to all of the other nodes specified in the params variable to have them register this node.
All registered nodes are also registered in their peers.

**Parameters:**
1. peers: list of IP address and Port tuples to register node with
```
{
    "action": "register_nodes",
    "params": [
        [
            ["<ip1>",<port1>],
            ["<ip2>",<port2>]
            ...
        ]
    ]
}
```

## **unregister_nodes**

**Description**:  
Unregisters peers with node through dispatcher thread

**Parameters:**
1. peers: list of IP address and Port tuples to unregister node with
```
{
    "action": "unregister_nodes",
    "params": [
        [
            ["<ip1>",<port1>],
            ["<ip2>",<port2>]
            ...
        ]
    ]
}
```

## **get_chain**

**Description**:  
Return the full blockchain for this node

**Parameters:** None
```
{
    "action": "get_chain",
    "params": []
}
```

## **get_chain_paginated**

**Description**:   
Return the blockchain of the node starting at the last block, and going to the first block in a paginated form with size "size".  
After sending this request, the node will send the last blocks in its chain with length "size"

**Parameters:**
1. size: size of the pagination

```
{
    "action": "get_chain_paginated",
    "params": [
        <amount>
    ]
}
```

**Client:**  
Continue to the next paginated block.   
Send: {"action": "inform", "params": {"message": "ACK"}}  
Response: {"section": &lt;section&gt;, "status": status} from the node

Stop receiving blocks  
Send: {"action": "inform", "params": {"message": "STOP"}}   
Response: None

**Statuses**:  
   * INITIAL: 
        - The initial section of the blockchain. Receiving this status after an 'INITIAL' status has already been sent before means that the chain has been replaced, and this new section is the new start of the chain  
   * CONTINUE: 
        - Continuation of the chain  
   * FINISHED:
        - End of the chain  
   * ERROR: 
        - An error has occured with the request. Size should be greater than 0 and an integer

## **get_block**

**Description:**  
Returns the block of the given node at a certain index
```
{
    "action": "get_block",
    "params": [
        <amount>
    ]
}
```

## **get_balance**

**Description:**  
Returns the wallet balance for the node
```
{
    "action": "get_balance",
    "params": []
}
```

## **resolve_conflicts**

**Description:**  
A special API endpoint that forces a specific node to becoming globally consistent. Resolve conflicts happens passively for every node when it receives a new block, but can be forced to be run in case the global state of the chain wants to be known to the outside world. 

**Parameters:** None
```
{
    "action": "resolve conflicts",
    "params": []
}
```
## **benchmark_initialize**

**Description**:  
This is a special API endpoint that isn't available unless the --benchmark flag is used. This endpoint initializes a specific node's history to have a certain amount of coins when the node is first run. A node in the benchmark mode needs to receieve this endpoint call in order to run. 

In benchmark mode, the client must send this request to all nodes in the system.

**Parameters:**
1. node_ids: a list of all nodes in the benchmark universe
2. value: The amount of money to initialize each node with
```
{
    "action": "benchmark_initialize",
    "params": [
        [
        [
            "<nodeid1>",
            "<nodeid2>",
            ...
        ],
        <amount>
    ]
}
```
