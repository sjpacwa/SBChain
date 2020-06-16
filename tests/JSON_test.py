"""
JSON_test.py

This test is responsible for testing the JSON decoder

2020 Stephen Pacwa and Daniel Okazaki
Santa Clara University
"""

# Standard library imports
import json

# Local imports
from coin import Coin
from encoder import ComplexEncoder
from transaction import Transaction

def test_complex_encoder_coin():
    coin = Coin("test", 1, "test2")

    json_obj = json.dumps(coin, cls=ComplexEncoder)

    assert json_obj == '{"uuid": "test2", "transaction_id": "test", "value": 1}'

def test_complex_encoder_coin_list():
    coin = [Coin("test", 1, "test2")]

    json_obj = json.dumps(coin, cls=ComplexEncoder)

    assert json_obj == '[{"uuid": "test2", "transaction_id": "test", "value": 1}]'

def test_complex_encoder_transaction():  
    inputs = [Coin("test", 1, "test")]
    outputs = {"1": [Coin("test", 1, "test2")]}

    transaction = Transaction("test", inputs, outputs, "test2", "time")

    json_obj = json.dumps(transaction, cls=ComplexEncoder)

    assert json_obj == '{"uuid": "test2", "timestamp": "time", "sender": "test", "inputs": [{"uuid": "test", "transaction_id": "test", "value": 1}], "outputs": {"1": [{"uuid": "test2", "transaction_id": "test", "value": 1}]}, "input_value": 1, "output_value": 1, "reward_value": 0}'
