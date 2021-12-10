import base58 as b58
import hashlib
import json
import sys
from rpc import get_receipt_proof, get_block
from dotmap import DotMap


def decode(value):
    return b58.b58decode(value)


def encode(value):
    return b58.b58encode(value)


# BASE_LIGHT_CLIENT_HEAD = '8ULrwa6swuPNEdRUu3d1ML66JQQkq1H2rNN8qwWxuxJd'
BASE_LIGHT_CLIENT_HEAD = 'Gxio7M6rc5FYEuXKEjAGHJs75Ye77A2RxmaavMXXJCcd'


def _get_next_block(block_id):
    cur = get_block(block_id)

    if 'error' in cur:
        if cur.error.cause.name == 'UNKNOWN_BLOCK':
            return _get_next_block(block_id + 1)
        else:
            raise cur

    return cur


def _get_range_forward(first_block, size):
    if size == 1:
        block = _get_next_block(first_block)
        return block.result.header.height + 1, decode(block.result.header.hash)
    else:
        next_block, left_hash = _get_range_forward(first_block, size // 2)
        next_block, right_hash = _get_range_forward(next_block, size // 2)
        return next_block, hashlib.sha256(left_hash + right_hash).digest()


def get_range_forward(first_block, size):
    return _get_range_forward(first_block, size)


def _get_range_backward(last_block, size):
    if size == 1:
        block = get_block(last_block)
        block_prev = get_block(block.result.header.prev_hash)
        return block_prev.result.header.hash, decode(block_prev.result.header.hash)
    else:
        prev_block, right_hash = _get_range_backward(last_block, size // 2)
        prev_block, left_hash = _get_range_backward(prev_block, size // 2)
        return prev_block, hashlib.sha256(left_hash + right_hash).digest()


def get_range_backward(last_block, size):
    return _get_range_backward(last_block, size)


def get_range(block_left, block_right):
    if block_right - block_left >= 16:
        return b'0'

    if block_left + 1 == block_right:
        return decode(get_block(block_left).result.header.hash)
    else:
        block_mid = (block_left + block_right) // 2
        left = get_range(block_left, block_mid)
        right = get_range(block_mid, block_right)
        return hashlib.sha256(left + right).digest()


def main():
    verify_intermidates_values = '--verify' in sys.argv

    with open(sys.argv[1]) as f:
        data = DotMap(json.load(f))

    print(data.description)
    receipt_id = data.receipt_id
    check(receipt_id, BASE_LIGHT_CLIENT_HEAD, verify_intermidates_values)


def check(receipt_id, base_light_client_head, verify_intermidates_values):
    block_base = get_block(base_light_client_head)
    block_merkle_root = block_base.result.header.block_merkle_root

    proof = get_receipt_proof(receipt_id, base_light_client_head)
    height = proof.result.block_header_lite.inner_lite.height

    block_cur = get_block(height)
    value = decode(block_cur.result.header.hash)

    left_block_id = height
    right_block_id = height + 1
    size = 1

    for step in proof.result.block_proof:
        inner = decode(step.hash)

        if step.direction == 'Right':
            raw = value + inner

            if verify_intermidates_values:
                right_block_id, hash = get_range_forward(right_block_id, size)
                hash = encode(hash).decode()
                print(f"{step.hash} == {hash}: {step.hash == hash}")
                assert step.hash == hash
        else:
            raw = inner + value

            if verify_intermidates_values:
                left_block_id, hash = get_range_backward(left_block_id, size)
                hash = encode(hash).decode()
                print(f"{step.hash} == {hash}: {step.hash == hash}")
                assert step.hash == hash

        size *= 2
        value = hashlib.sha256(raw).digest()

    found_merkle_root = encode(value).decode()
    print('Found merkle root:   ', found_merkle_root)
    print('Expected merkle root:', block_merkle_root)

    assert(found_merkle_root == block_merkle_root)
    print("Block proof correct")


def find_epoch_change():
    block = 54544199

    epoch_id = get_block(block).result.header.epoch_id

    lo = block
    hi = block + 10**6

    while lo + 1 < hi:
        mid = (lo + hi) // 2
        cur_epoch_id = get_block(mid).result.header.epoch_id

        if epoch_id == cur_epoch_id:
            lo = mid
        else:
            hi = mid

    print(lo, hi)


if __name__ == '__main__':
    lo = 54544200
    hi = 54544200 + 43200
    receipt_id = 'FGomjRJeHc3zacoDoxbKJ2bTm9BZ2q5Bn4jjkUqskZEp'

    while lo + 1 < hi:
        print(lo, hi, hi - lo)
        mid = (lo + hi) // 2

        block_head = get_block(mid).result.header.hash

        try:
            check(receipt_id, block_head, False)
            ok = True
        except:
            ok = False

        if ok:
            lo = mid
        else:
            hi = mid

    print(lo, hi)
    # main()
