import requests
import json
from dotmap import DotMap
from utils import memo
from functools import lru_cache

url = "https://archival-rpc.mainnet.near.org/"

headers = {
    'Content-Type': 'application/json'
}


@lru_cache(None)
@memo
def get_block(block_id):
    payload = json.dumps({
        "jsonrpc": "2.0",
        "id": "dontcare",
        "method": "block",
        "params": {
            "block_id": block_id
        }
    })
    response = requests.request("POST", url, headers=headers, data=payload)
    return DotMap(response.json())


@lru_cache(None)
@memo
def get_receipt_proof(receipt_id, light_client_head, receiver_id='aurora'):
    payload = json.dumps({
        "jsonrpc": "2.0",
        "id": "dontcare",
        "method": "EXPERIMENTAL_light_client_proof",
        "params": {
            "type": "receipt",
            "receipt_id": receipt_id,
            "receiver_id": receiver_id,
            "light_client_head": light_client_head
        }
    })
    response = requests.request("POST", url, headers=headers, data=payload)
    return DotMap(response.json())
