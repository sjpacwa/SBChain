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
	RESPONSE_BLOCK = 2
	RESPONSE_BLOCKCHAIN = 3
	QUERY_TRANSACTIONS = 4
	RESPONSE_TRANSACTIONS = 5


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
	return Message(MessageType.RESPONSE_BLOCK,
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

def resolve_conflicts(new_chain):
		"""
		This is our consensus algorithm, it resolves conflicts
		by replacing our chain with the longest one in the network.

		:return: True if our chain was replaced, False if not
		"""

		# We're only looking for chains longer than ours.
		max_length = len(node.blockchain.chain)

		# Compare length of sent chain with the current chain.
		if len(new_chain) > max_length and node.blockchain.valid_chain(new_chain):
			if len(new_chain) == 1:
				await broadcast( query_all_msg )
				return
			self.blockchain.chain = new_chain
			self.blockchain.chain_dict = new_chain
			print('Peer\'s chain was larger, replacing ours')
		else:
			print('Our chain was larger or the same than our peer\'s')

def check_block(new_block):
	if node.blockchain.chain[-1].hash() == new_block.previous_hash:
		print('Another node has mined a block')
		node.blockchain.chain.append(new_block)
		await broadcast_latest()

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
				new_chain = [ block.generate_block_from_json(b) for b in recv_msg.data ]
				await resolve_conflicts(new_chain)
				
			elif recv_msg.type == msg_type.RESPONSE_BLOCK:
				new_block = block.generate_block_from_json(recv_msg.data[0])
				await check_block(new_block)

			elif recv_msg.type == msg_type.QUERY_TRANSACTIONS:
				await  ws.send_str(resp_tx_msg())

			elif recv_msg.type == msg_type.RESPONSE_TRANSACTIONS:
				received_pool = [ node.blockchain.new_transaction(**json.loads(j)) for j in recv_msg.data]
				if len(received_pool) <= 0:
					log.warning("Received txpool is empty")
				else:
					for t in received_pool:
						if t not in node.blockchain.current_transactions:
							node.blockchain.current_transactions.append(t)
					await broadcast_tx()
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