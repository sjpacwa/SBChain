"""
p2p.py
This file is responsible for defining peer to peer interactions between nodes
in the blockchain.
"""

import logging
import json
import asyncio

from aiohttp import web

from block import Block
from blockchain import Blockchain
from node import Node

log = logging.getLogger(__name__)
peers = {}


class MessageType(object):
	QUERY_LATEST = 0
	QUERY_ALL = 1
	RESPONSE_BLOCKCHAIN = 2
	QUERY_TRANSACTIONS = 3
	RESPONSE_TRANSACTIONS = 4


class Message(object):
	def __init__(self, type, data):
		self.type = type
		self.data = data

	def to_json(self):
		return json.dumps({
			"type": self.type,
			"data": self.data
		})

# Message object to query for all blocks.
query_all_msg = Message(MessageType.QUERY_ALL, data=None).to_json()

# Message object to query for latest block.
query_latest_msg = Message(MessageType.QUERY_LATEST, data=None).to_json()

# Message object to query for transactions.
query_tx_msg = Message(MessageType.QUERY_TRANSACTIONS, data=None).to_json()

def get_msg_from_json(json_str):
	msg_json = json.loads(json_str)
	return Message(msg_json['type'], msg_json['data'])

def resp_latest_message(node):
	"""
	:return: msg object with lastest block-json as data
	"""
	log.info("Generating latest block response json")
	return Message(MessageType.RESPONSE_BLOCKCHAIN,
			   [ node.blockchain.last_block().to_json() ]
			   ).to_json()

def resp_chain_message(node):
	"""
	:return: msg object with list if json-blocks as data
	"""
	log.info("Generating blockchain response json")
	return Message(MessageType.RESPONSE_BLOCKCHAIN,
			   [block.to_json() for block in node.blockchain.chain]
			   ).to_json()

def resp_tx_msg():
	"""
	:return: list of tx objects
	"""
	return Message(MessageType.RESPONSE_TRANSACTIONS,
			   [json.dump(tx) for tx in node.blockchain.current_transactions]
			   ).to_json()

"""
async def handle_blockchain_resp(new_chain):
	if len(new_chain) == 0:
		log.info("New received chain len is 0")
		return

	our_last_blk = block.get_latest_block()
	got_last_blk = new_chain[-1]

	# if more blocks in new chain
	if our_last_blk.index < got_last_blk.index:
		log.info("Got new chain with len: {}, ours is: {}".format(len(new_chain), len(blockchain.blockchain)))

		if our_last_blk.hash == got_last_blk.prev_hash:
			log.info("We were one block behind, adding new block")
			block.add_block_to_blockchain(got_last_blk)
			await broadcast_latest()
		elif len(new_chain) == 1:
			log.info("Got just one block. gonna query whole chain")
			await broadcast( query_all_msg )
		else:
			log.info("Received longer chain, replacing")
			await blockchain.replace_chain(new_chain)
	else:
		log.info("Shorter blockchain received, do nothing")
"""

async def handle_peer_msg(key, ws):
	await ws.send_str(query_latest_msg)
	await asyncio.sleep(0.5)
	await ws.send_str(query_tx_msg)

	async for ws_msg in ws:
		if ws_msg.type == web.WSMsgType.text:
			msg_data = ws_msg.data
			log.info("Got message: {}".format(msg_data))
			recv_msg = get_msg_from_json(msg_data)

			# Respond according to message types.
			if recv_msg.type == msg_type.QUERY_LATEST:
				await ws.send_str(resp_latest_message())

			elif recv_msg.type == msg_type.QUERY_ALL:
				await ws.send_str(resp_chain_message())

			elif recv_msg.type == msg_type.RESPONSE_BLOCKCHAIN:
				pass
				"""
				new_chain = [ block.generate_block_from_json(b) for b in recv_msg.data ]
				await handle_blockchain_resp(new_chain)
				"""

			elif recv_msg.type == msg_type.QUERY_TRANSACTIONS:
				await  ws.send_str(resp_tx_msg())

			elif recv_msg.type == msg_type.RESPONSE_TRANSACTIONS:
				received_pool = [ node.blockchain.new_transaction(**json.loads(j)) for j in recv_msg.data]
				if len(received_pool) <= 0:
					log.warning("Received txpool is empty")
				else:
					for t in received_pool:
						try:
							# TODO Validate the transaction.
							transact_pool.add_to_transact_pool(t, blockchain.utxo)
							await broadcast_txpool()
						except Exception:
							log.warning("Received pool was not added")
		elif ws_msg.type == web.WSMsgType.binary:
			log.info("Binary message; ignoring...")
		elif ws_msg.type in [web.WSMsgType.close, web.WSMsgType.error]:
			log.info("WS close or err: closing connection")
			peers[key].close()
			del peers[key]

async def broadcast(data, node):
	log.info("Broadcasting: {}".format(data))
	for p in node.nodes:
		log.info("Broadcasting to: {}".format(p))
		await node.nodes[p].send_str(data)

async def broadcast_latest():
	log.info("Broadcasting latest block")
	data = resp_latest_message()
	await broadcast(data)

async def broadcast_tx():
	log.info("Broadcasting tx")
	data = resp_tx_msg()
await broadcast(data)