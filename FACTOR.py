import ctypes
import urllib.request
import urllib.error
import urllib.parse
import base64
import json
import hashlib
import struct
import random
import os
import sys
import struct
import sympy as sp
import gmpy2 as gmp
from math import floor, ceil
from gmpy2 import mpz,mpq,mpfr,mpc
from gmpy2 import isqrt, sqrt, log2, gcd
from numpy.ctypeslib import ndpointer
import subprocess
import random
from time import time
import multiprocessing
import hashlib
import pebble
import base58

#Attibution note: the Bitcoin RPC components here are taken
#                 from publicly available sources and are not
#                 my own original code.

#Factoring libraries
import cypari2 as cp
cyp = cp.Pari()
cyp.default("parisizemax", 1<<29 )
cfactor = cyp.factorint

# This gives direct access to the integer factoring engine called by most arithmetical functions. flag is optional; its binary digits mean 
# 1: avoid MPQS, 
# 2: skip first stage ECM (we may still fall back to it later), 
# 4: avoid Rho and SQUFOF, 
# 8: don’t run final ECM (as a result, a huge composite may be declared to be prime). 
#    Note that a (strong) probabilistic primality test is used, thus composites might not be detected, although no example is known.

#Flags
SKIP_MPQS          = 1
SKIP_ECM_STAGE_ONE = 2
SKIP_RO_SQUFOF     = 4
SKIP_ECM_STAGE_TWO = 8

#HTML Parsing Library 
from bs4 import BeautifulSoup

RPC_URL = os.environ.get("RPC_URL", "http://127.0.0.1:8332")
RPC_USER = os.environ.get("RPC_USER", "rpcuser")
RPC_PASS = os.environ.get("RPC_PASS", "rpcpass") 

################################################################################
# CTypes and utility functions
################################################################################
class CParams(ctypes.Structure):
    _fields_=[("hashRounds",ctypes.c_uint32 ),
              ("MillerRabinRounds",ctypes.c_uint32 )  
             ]
    
class uint1024(ctypes.Structure):
    _fields_=[("data", ctypes.c_uint64 * 16 )]

class uint256(ctypes.Structure):
    _fields_=[("data", ctypes.c_uint64 * 4 )]
    
def uint256ToInt( m ):
    ans = 0    
    for idx,a in enumerate(m):
        ans += a << (idx*64)
    return ans

def uint1024ToInt( m ):
    ans = 0    

    if hasattr(m, 'data'):
        for idx in range(16):
            ans += m.data[idx] << (idx*64)
    else:
        for idx,a in enumerate(m):
            ans += a << (idx*64)
    
    return ans

def IntToUint1024( m ):
    ans = [0]*16
    n = int(m)
    MASK = (1<<64)-1
    
    for idx in range(16):
        ans[idx] = (m >> (idx*64)) & MASK
    
    return (ctypes.c_uint64 * 16)(*ans)
    
    
def hashToArray( Hash ):
    if Hash == 0:
        return [0,0,0,0]
    
    number = int(Hash,16)
    MASK = (1 << 64) - 1
    arr = [ ( number >> 64*(jj) )&MASK for jj in range(0, 4) ]    
    
    return arr


################################################################################
# Bitcoin Daemon JSON-HTTP RPC
################################################################################


def rpc(method, params=None):
    """ 
    Make an RPC call to the Bitcoin Daemon JSON-HTTP server.

    Arguments:
        method (string): RPC method
        params: RPC arguments

    Returns:
        object: RPC response result.
    """

    rpc_id = random.getrandbits(32)
    data = json.dumps({"id": rpc_id, "method": method, "params": params}).encode()
    auth = base64.encodebytes((RPC_USER + ":" + RPC_PASS).encode()).decode().strip()

    request = urllib.request.Request(RPC_URL, data, {"Authorization": "Basic {:s}".format(auth)})

    with urllib.request.urlopen(request) as f:
        response = json.loads(f.read())

    if response['id'] != rpc_id:
        raise ValueError("Invalid response id: got {}, expected {:u}".format(response['id'], rpc_id))
    elif response['error'] is not None:
        raise ValueError("RPC error: {:s}".format(json.dumps(response['error'])))

    return response['result']

################################################################################
# Bitcoin Daemon RPC Call Wrappers
################################################################################


def rpc_getblocktemplate():
    try:
        return rpc("getblocktemplate", [{"rules": ["segwit"]}])
    except ValueError:
        return {}


def rpc_submitblock(block_submission):
    return rpc("submitblock", [block_submission])


def rpc_getblockcount():
    return rpc( "getblockcount" )


################################################################################
# Representation Conversion Utility Functions
################################################################################


def int2lehex(value, width):
    """
    Convert an unsigned integer to a little endian ASCII hex string.
    Args:
        value (int): value
        width (int): byte width
    Returns:
        string: ASCII hex string
    """

    return value.to_bytes(width, byteorder='little').hex()


def int2varinthex(value):
    """
    Convert an unsigned integer to little endian varint ASCII hex string.
    Args:
        value (int): value
    Returns:
        string: ASCII hex string
    """

    if value < 0xfd:
        return int2lehex(value, 1)
    elif value <= 0xffff:
        return "fd" + int2lehex(value, 2)
    elif value <= 0xffffffff:
        return "fe" + int2lehex(value, 4)
    else:
        return "ff" + int2lehex(value, 8)


def bitcoinaddress2hash160(addr):
    """
    Convert a Base58 Bitcoin address to its Hash-160 ASCII hex string.
    Args:
        addr (string): Base58 Bitcoin address
    Returns:
        string: Hash-160 ASCII hex string
    """

    table = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

    hash160 = 0
    addr = addr[::-1]
    for i, c in enumerate(addr):
        hash160 += (58 ** i) * table.find(c)

    # Convert number to 50-byte ASCII Hex string
    hash160 = "{:050x}".format(hash160)

    # Discard 1-byte network byte at beginning and 4-byte checksum at the end
    return hash160[2:50 - 8]

################################################################################
# Transaction Coinbase and Hashing Functions
################################################################################


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

    print( bytes([width]).hex()     )
    print( int2lehex(height, width) )
    
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
    
def tx_make_coinbase(coinbase_script, pubkey_script, value, height):
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
    print("Coinbase height: ", tx_encode_coinbase_height(height), "   Height: ", height )
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
    tx += "01"
    # output[0] value
    tx += int2lehex(value, 8)
    # output[0] script len
    tx += int2varinthex(len(pubkey_script) // 2)
    # output[0] script
    tx += pubkey_script
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

################################################################################
# Bitcoin Core Wrappers
################################################################################
class CBlock(ctypes.Structure):
    blocktemplate = {}
    _hash = "0"*32
    _fields_ = [("nP1",                 ctypes.c_uint64 * 16),
              ("hashPrevBlock",       ctypes.c_uint64 * 4 ),
              ("hashMerkleRoot",      ctypes.c_uint64 * 4 ),
              ("nNonce",   ctypes.c_uint64),
              ("wOffset",  ctypes.c_int64),
              ("nVersion", ctypes.c_uint32),
              ("nTime",    ctypes.c_uint32),
              ("nBits",    ctypes.c_uint16),
             ]

    
    def get_next_block_to_work_on(self):
        blocktemplate      = rpc_getblocktemplate()
        self.blocktemplate = blocktemplate 

        prevBlock = blocktemplate["previousblockhash"]
        prevBlock = hashToArray(prevBlock)

        merkleRoot = blocktemplate["merkleroothash"]
        merkleRoot = hashToArray(merkleRoot)

        self.nP1                 = (ctypes.c_uint64 * 16)(*([0]*16))
        self.hashPrevBlock       = (ctypes.c_uint64 * 4)(*prevBlock)
        self.hashMerkleRoot      = (ctypes.c_uint64 * 4)(*merkleRoot )
        self.nNonce   = 0
        self.nTime    = ctypes.c_uint32( blocktemplate["curtime"] )
        self.nVersion = ctypes.c_uint32( blocktemplate["version"] )
        self.nBits    = ctypes.c_uint16( blocktemplate["bits"] )
        self.wOffset  = 0
        
        return self
    
    def serialize_block_header(self):
        #Get the data
        nP1                 = hex(uint1024ToInt(self.nP1)                 )[2:].zfill(256)
        hashPrevBlock       = hex(uint256ToInt( self.hashPrevBlock)       )[2:].zfill(64)
        hashMerkleRoot      = hex(uint256ToInt( self.hashMerkleRoot)      )[2:].zfill(64)
        nNonce              = struct.pack("<Q", self.nNonce)
        wOffset             = struct.pack("<q", self.wOffset)
        nVersion            = struct.pack("<L", self.nVersion)
        nTime               = struct.pack("<L", self.nTime)
        nBits               = struct.pack("<H", self.nBits)
        
        #Reverse bytes of the hashes as little-Endian is needed for bitcoind
        nP1                 = bytes.fromhex(nP1)[::-1]
        hashPrevBlock       = bytes.fromhex(hashPrevBlock)[::-1] 
        hashMerkleRoot      = bytes.fromhex(hashMerkleRoot)[::-1]
                                                
        #Serialize in the right order
        CBlock1 = bytes()
        CBlock1 += nP1
        CBlock1 += hashPrevBlock
        CBlock1 += hashMerkleRoot
        CBlock1 += nNonce
        CBlock1 += wOffset
        CBlock1 += nVersion
        CBlock1 += nTime
        CBlock1 += nBits
        
        return CBlock1
    
    def __str__(self):
        
        #Get the data
        nP1                 = hex(uint1024ToInt(self.nP1)                 )[2:].zfill(256)
        hashPrevBlock       = hex(uint256ToInt( self.hashPrevBlock)       )[2:].zfill(64)
        hashMerkleRoot      = hex(uint256ToInt( self.hashMerkleRoot)      )[2:].zfill(64)
        nNonce              = struct.pack("<Q", self.nNonce).hex()
        wOffset             = struct.pack("<q", self.wOffset).hex()
        nVersion            = struct.pack("<L", self.nVersion).hex()
        nTime               = struct.pack("<L", self.nTime).hex()
        nBits               = struct.pack("<H", self.nBits).hex()
        
        #Reverse bytes of the hashes as little-Endian is needed for bitcoind
        nP1                 = bytes.fromhex(nP1)[::-1].hex()
        hashPrevBlock       = bytes.fromhex(hashPrevBlock)[::-1].hex() 
        hashMerkleRoot      = bytes.fromhex(hashMerkleRoot)[::-1].hex()
        
        s  = "CBlock class: \n"
        s += "                    nP1: " + str(nP1)                 + "\n"
        s += "          hashPrevBlock: " + str(hashPrevBlock)       + "\n"
        s += "         hashMerkleRoot: " + str(hashMerkleRoot)      + "\n"
        s += "                 nNonce: " + str(nNonce)              + "\n"
        s += "                wOffset: " + str(wOffset)             + "\n"
        s += "               nVersion: " + str(nVersion)            + "\n"
        s += "                  nTime: " + str(nTime)               + "\n"
        s += "                  nBits: " + str(nBits)               + "\n"
    
        return s
    
    def int2lehex(self, value, width):
        """
        Convert an unsigned integer to a little endian ASCII hex string.
        Args:
            value (int): value
            width (int): byte width
        Returns:
            string: ASCII hex string
        """

        return value.to_bytes(width, byteorder='little').hex()

    def int2varinthex(self, value):
        """
        Convert an unsigned integer to little endian varint ASCII hex string.
        Args:
            value (int): value
        Returns:
            string: ASCII hex string
        """

        if value < 0xfd:
            return self.int2lehex(value, 1)
        elif value <= 0xffff:
            return "fd" + self.int2lehex(value, 2)
        elif value <= 0xffffffff:
            return "fe" + self.int2lehex(value, 4)
        else:
            return "ff" + self.int2lehex(value, 8)

    def prepare_block_for_submission(self):
        #Get block header
        submission = self.serialize_block_header().hex()
        
        # Number of transactions as a varint
        submission += self.int2varinthex(len(self.blocktemplate['transactions']))
        
         # Concatenated transactions data
        for tx in self.blocktemplate['transactions']:
            submission += tx['data']
            
        return submission
    
    def rpc_submitblock(self):
        submission = self.prepare_block_for_submission()
        return rpc_submitblock(submission), submission
    
    def compute_raw_hash(self):
        """
        Compute the raw SHA256 double hash of a block header.
        Arguments:
            header (bytes): block header
        Returns:
            bytes: block hash
        """

        return hashlib.sha256(hashlib.sha256(self.serialize_block_header()).digest()).digest()[::-1]

    #WARNING: the default scriptPubKey here is for a testing wallet.
    #TODO: replace and raise an error if no scriptPubKey is given for master branch.
    def mine(self, load=True, mine_latest_block = True, coinbase_message = "", scriptPubKey = "00147d2af2ad52307c7c343729b5f09ccac96a35e503"):
        print("Setup Start...", flush=True)
        START = time()

        #Get parameters and candidate block
        block = None
        param = getParams()
        
        if mine_latest_block:
            block = self.get_next_block_to_work_on()
        else:
            block = self
            block.nBits = 180
            block.blocktemplate['coinbasevalue'] = 0
            block.blocktemplate['height'] = 0
            block.blocktemplate['transactions'] = []
            block.blocktemplate['merkleroot'] = "0x0000000000000000000000000000000000000000000000000000000000000000"

        # Add an coinbase transaction to the block template transactions
        coinbase_tx = {}

        # Update the coinbase transaction with the new extra nonce
        coinbase_script = coinbase_message 
        coinbase_tx['data'] = tx_make_coinbase(coinbase_script, scriptPubKey, block.blocktemplate['coinbasevalue'], block.blocktemplate['height'])
        coinbase_tx['hash'] = tx_compute_hash(coinbase_tx['data'])

        #Add transaction to our block
        block.blocktemplate['transactions'].insert(0, coinbase_tx)
        
        # Recompute the merkle root
        block.blocktemplate['merkleroot'] = tx_compute_merkle_root([tx['hash'] for tx in block.blocktemplate['transactions']])   
        merkleRoot = uint256()
        merkleRoot = (ctypes.c_uint64 * 4)(*hashToArray( block.blocktemplate["merkleroot"]  if mine_latest_block else "6a3ae329ed61aee656ddbe14d8b2878125e96d0900ac0bb4c20c4f3300fb68d3") )
        block.hashMerkleRoot = merkleRoot

        #Iterate through a small set of random nonces
        #Probability of finding a good semiprime is extremely high
        Seeds = [ random.randint(0,1<<64) for i in range(100)] if mine_latest_block else list(range(100))

        #Compute sieving wheel for stepping through W's range
        wheel = [ k for k in range(1, sieve_level1) if gcd(k,2*3*5)==1]

        for nonce in Seeds:
            start = time()
            print("Nonce: ", nonce, flush=True)
            #Set the nonce
            block.nNonce = nonce

            #Get the W
            W = gHash(block,param)
            W = uint1024ToInt(W)

            #Compute limit range around W
            print("nBits: ", block.nBits )
            wInterval = 16 * block.nBits 
            wMAX = int(W + wInterval)
            wMIN = int(W - wInterval) 
            
            print( "Interval to consider has " + str(fD) + " candidates." ,flush=True)

            #Candidates for admissible semiprime
            candidates = [ a for a in range( wMIN, wMin) if  ( abs(a-W) > wInterval) and (abs(a-w)%2 != 0 ) ] 
            
            print("Checking candidates are exactly " + str(block.nBits) + " binary digits long.")
            
            #Make sure the candidates have exactly nBits as required by this block
            candidates = [ k for k in candidates if k.bit_length() == block.nBits ] #This line requires python >= 3.10

            print("Survivors: ", len(candidates) )

            #Random shuffle candidates
            random.shuffle(candidates)      

            kstart = time()
            check_race = 0
            for idx, n in enumerate( candidates ):
                #Check if the current block race has been won already
                if check_race % 12 == 0:
                    if rpc_getblockcount() + 1 != block.blocktemplate["height"]:
                        print("Race was lost. Next block.")
                        print("Total Block Mining Runtime: ", time() - START, " Seconds." )
                        return None
                check_race += 1

                f = cfactor(n)
                factors = [ int(a) for a in f[0]]
                power   = f[1]

                if   (len(factors) == 2):
                    print( " {:> 5d} {:> 5d} {:> 5d} {:> 5d} {:> 3.3f} Seconds".format( idx, len(factors), factors[0].bit_length(), block.nBits//2, time()-kstart ), flush=True )

                    if ( factors[0].bit_length() == block.nBits//2 ):
                        print( factors, nonce )

                        #Update values for the found block
                        block.nP1     = IntToUint1024(factors[0])
                        block.nNonce  = nonce
                        block.wOffset = n - W

                        #Compute the block hash
                        block_hash = block.compute_raw_hash()

                        #Update block
                        block._hash = block_hash
                        
                        print("      N: ", n)
                        print("      W: ", W)
                        print("wOffset: ", n - W)
                        print("Total Block Mining Runtime: ", time() - START, " Seconds." )
                        print()
                        print()

                        return block

            print("Runtime: ", time() - start )
            
def getParams():
    param = CParams()
    param.hashRounds = 1
    param.MillerRabinRounds = 50
    return param

gHash = ctypes.CDLL("./gHash.so").gHash
gHash.restype = uint1024

def mine():
    while True:
        B = CBlock()
        if B.mine( load=True, mine_latest_block=True):
            B.rpc_submitblock()
        print(B)
