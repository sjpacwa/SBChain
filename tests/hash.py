import hashlib
import json
from datetime import datetime
string = {'index': 1, 'previous_hash': '1', 'proof': 100, 'timestamp': '0001-01-01T00:00:00Z', 'transactions': []}
string = json.dumps(string,indent=4,sort_keys=True,default=str).encode()

string2_receieved = {'index': 2, 'previous_hash': '3ef1ec27d95fe0113193d3247662581f7a9b8e54af230076f14c58940b0cfebb', 'proof': 237974, 'timestamp': '2019-12-23T16:33:23Z', 'transactions': []}
string2_receieved = json.dumps(string2_receieved,indent=4,sort_keys=True,default=str).encode()

string2_sent_transac_on = {'index': 2, 'previous_hash': '54d8e4422466518fdd283ea7b8ebe491c1a3786ea7efb247fb4450db5da76b47', 'proof': 59793, 'timestamp': '0001-01-01T00:00:00Z', 'transactions': [{'sender': '0', 'recipient': 'a713ee88596f43dab0f1e87462a7c3c6', 'amount': 1, 'timestamp': '2019-12-23T15:47:23Z'}]}
string2_sent_transac_on = json.dumps(string2_sent_transac_on,indent=4,sort_keys=True,default=str).encode()


string2_send_transac_off = {'index': 2, 'previous_hash': '3ef1ec27d95fe0113193d3247662581f7a9b8e54af230076f14c58940b0cfebb', 'proof': 237974, 'timestamp': '2019-12-23T16:33:23Z', 'transactions': []}
string2_send_transac_off = json.dumps(string2_send_transac_off,indent=4,sort_keys=True,default=str).encode()

print("Genesis")
print(hashlib.sha256(string).hexdigest())
print("Receieved:")
print(hashlib.sha256(string2_receieved).hexdigest())
#print(hashlib.sha256(string2_sent_transac_on).hexdigest()
print("Sent")
print(hashlib.sha256(string2_send_transac_off).hexdigest())

print(datetime.min.strftime('%Y-%m-%dT%H:%M:%SZ'))