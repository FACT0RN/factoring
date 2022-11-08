################################################################################
# Transaction Coinbase and Hashing Functions
################################################################################
import hashlib
import base58
from lib.repr import *


def tx_encode_coinbase_height(height):
    """
    Encode the coinbase height, as per BIP 34:
    https://github.com/bitcoin/bips/blob/master/bip-0034.mediawiki
    Arguments:
        height (int): height of the mined block
    Returns:
        string: encoded height as an ASCII hex string
    """

    width = (height.bit_length() + 7 )//8 

    return bytes([width]).hex() + int2lehex(height, width)

def make_P2PKH_from_public_key( publicKey = "03564213318d739994e4d9785bf40eac4edbfa21f0546040ce7e6859778dfce5d4" ):
    from hashlib import sha256 as sha256
   
    address   = sha256( bytes.fromhex( publicKey) ).hexdigest()
    address   = hashlib.new('ripemd160', bytes.fromhex( address ) ).hexdigest()
    address   = bytes.fromhex("00" + address)
    addressCS = sha256(                address     ).hexdigest()
    addressCS = sha256( bytes.fromhex( addressCS ) ).hexdigest()
    addressCS = addressCS[:8]
    address   = address.hex() + addressCS
    address   = base58.b58encode( bytes.fromhex(address))
    
    return address
    
def tx_make_coinbase(coinbase_script, pubkey_script, value, height, wit_commitment):
    """
    Create a coinbase transaction.
    Arguments:
        coinbase_script (string): arbitrary script as an ASCII hex string
        address (string): Base58 Bitcoin address
        value (int): coinbase value
        height (int): mined block height
    Returns:
        string: coinbase transaction as an ASCII hex string
    """
    # See https://en.bitcoin.it/wiki/Transaction
    coinbase_script = tx_encode_coinbase_height(height) + coinbase_script

    tx = ""
    # version
    tx += "02000000"
    # in-counter
    tx += "01"
    # input[0] prev hash
    tx += "0" * 64
    # input[0] prev seqnum
    tx += "ffffffff"
    # input[0] script len
    tx += int2varinthex(len(coinbase_script) // 2)
    # input[0] script
    tx += coinbase_script
    # input[0] seqnum
    tx += "00000000"
    # out-counter
    tx += "02"
    # output[0] value
    tx += int2lehex(value, 8)
    # output[0] script len
    tx += int2varinthex(len(pubkey_script) // 2)
    # output[0] script
    tx += pubkey_script
    # witness commitment value
    tx += int2lehex(0, 8)
    # witness commitment script len
    tx += int2varinthex(len(wit_commitment) // 2)
    # witness commitment script
    tx += wit_commitment
    # lock-time
    tx += "00000000"

    return tx


def tx_compute_hash(tx):
    """
    Compute the SHA256 double hash of a transaction.
    Arguments:
        tx (string): transaction data as an ASCII hex string
    Return:
        string: transaction hash as an ASCII hex string
    """

    return hashlib.sha256(hashlib.sha256(bytes.fromhex(tx)).digest()).digest()[::-1].hex()


def tx_compute_merkle_root(tx_hashes):
    """
    Compute the Merkle Root of a list of transaction hashes.
    Arguments:
        tx_hashes (list): list of transaction hashes as ASCII hex strings
    Returns:
        string: merkle root as a big endian ASCII hex string
    """
    
    # Convert list of ASCII hex transaction hashes into bytes
    tx_hashes = [bytes.fromhex(tx_hash)[::-1] for tx_hash in tx_hashes]

    # Iteratively compute the merkle root hash
    while len(tx_hashes) > 1:
        # Duplicate last hash if the list is odd
        if len(tx_hashes) % 2 != 0:
            tx_hashes.append(tx_hashes[-1])

        tx_hashes_new = []

        for i in range(len(tx_hashes) // 2):
            # Concatenate the next two
            concat = tx_hashes.pop(0) + tx_hashes.pop(0)
            # Hash them
            concat_hash = hashlib.sha256(hashlib.sha256(concat).digest()).digest()
            # Add them to our working list
            tx_hashes_new.append(concat_hash)

        tx_hashes = tx_hashes_new

    # Format the root in big endian ascii hex
    return tx_hashes[0][::-1].hex()
