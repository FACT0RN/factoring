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
#import sympy as sp
import gmpy2 as gmp
from math import floor, ceil
from gmpy2 import mpz,mpq,mpfr,mpc
from gmpy2 import is_square, isqrt, sqrt, log2, gcd, is_prime, next_prime
from numpy.ctypeslib import ndpointer
import subprocess
import random
from time import time
import multiprocessing
import hashlib
import base58
from number_theory import *
#Attibution note: the Bitcoin RPC components here are taken
#                 from publicly available sources and are not
#                 my own original code.


pid = os.getpid()
fp = open("factoring_%d.log" % pid,"a")

RPC_PORT     = os.environ.get("RPC_PORT", "8332")
RPC_URL      = os.environ.get("RPC_URL", "http://127.0.0.1:"+ str(RPC_PORT) )
RPC_USER     = os.environ.get("RPC_USER", "rpcuser")
RPC_PASS     = os.environ.get("RPC_PASS", "rpcpass") 
SCRIPTPUBKEY = os.environ.get("SCRIPTPUBKEY") 

SIEVE_MAX_LEVEL = os.environ.get("SIEVE_MAX_LEVEL")
if SIEVE_MAX_LEVEL == None: 
  SIEVE_MAX_LEVEL = 31
else:
  SIEVE_MAX_LEVEL = int(SIEVE_MAX_LEVEL)
siever = prime_levels_load(4, SIEVE_MAX_LEVEL) 
base_primorial = 2*3*5*7*11*13 


#Check that a standard scriptPybKey has been passed. This is a simple check
#to help avoid mistakes and losing coins. If you know enough to complain
#about not allowing other types of scriptPubKey then you know enough
#to modify this and make it suit your needs.
if SCRIPTPUBKEY == None:
    print("Your scriptPubKey has not been set. Set the environmental variable SCRIPTPUBKEY with a scriptPubKey from any address in your wallet.")
    exit(1)

if ( len(SCRIPTPUBKEY) != 44 ):
    print("Your scriptPubKey ("+str(SCRIPTPUBKEY)+") is not a standard 22 byte scriptPubKey.")
    print("Please check and verify this is correct. Your mining rewards will be lost if you proceed with scriptPubKey address.")
    exit(2)

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

Count = 0
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

   
    def build_pow(self, block, W, n, factors, nonce, idx):
        pdiff = abs(factors[0].bit_length() - factors[1].bit_length())
        print("Factors bit diff: %d" % pdiff)
        if ( factors[0].bit_length() == ( block.nBits//2 + (block.nBits&1)) ):
          print( " {:> 5d} {:> 5d} {:> 5d} {:> 5d} {:> 3.3f} Seconds".format( idx, len(factors), factors[0].bit_length(), block.nBits//2, time()-self.kstart ), flush=True )
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
          print("      P: ", factors[0])
          print("wOffset: ", block.wOffset)
          print("Total Block Mining Runtime: ", time() - self.START, " Seconds." )
          global fp
          fp.write("Found block_hash: %s\n" % str(block_hash.hex()))
          fp.flush()
          self.Found += 1
          return block

    
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
    def mine(self, mine_latest_block = True, coinbase_message = "", scriptPubKey = None ):
        global fp, primorial_base, siever, SIEVE_MAX_LEVEL
        self.Count = 0
        self.Found = 0
        #Check a value was passed for scriptPubKey
        if not scriptPubKey:
            raise ValueError('Please provide a scriptPubKey to allow you to earn rewards for mining. See README.')
        if len(scriptPubKey) < 30:
            raise ValueError('Please check your scriptPubKey is correct. It is unlikely to be less than 30 characters long.')

        self.START = time()

        #Get parameters and candidate block
        block = None
        param = getParams()
        
        if mine_latest_block:
            block = self.get_next_block_to_work_on()
        else:
            block = self
            block.nBits = 69
            block.nVersion = 0
            block.nTime = 1649693313
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
        merkleRoot = (ctypes.c_uint64 * 4)(*hashToArray( block.blocktemplate["merkleroot"] if mine_latest_block else "6a3ae329ed61aee656ddbe14d8b2878125e96d0900ac0bb4c20c4f3300fb68d3")) 
        block.hashMerkleRoot = merkleRoot

        #Iterate through a small set of random nonces
        #Probability of finding a good semiprime is extremely high
        Seeds = [ random.randint(0,1<<64) for i in range(10000)] if mine_latest_block else list(range(10000))

        for nonce in Seeds:
            start = time()
            #Set the nonce
            block.nNonce = nonce

            #Get the W
            W = gHash(block,param)
            W = uint1024ToInt(W)
 
            print("=" * 80)
            print("W: %d" % W)

            #Compute limit range around W
            wInterval = 16 * block.nBits 
            wMAX = int(W + wInterval)
            wMIN = int(W - wInterval) 

            #Candidates for admissible semiprime
            candidates = [ a for a in range( wMIN, wMAX) if gcd( a, base_primorial ) == 1 and not is_prime(a)  ]

            #Sieve up to level 20 by default.
            ss1 = time()
            for level in range(4,SIEVE_MAX_LEVEL):
                s1 = time()
                candidates = [ n for n in candidates if gcd(siever[level], n ) == 1  ] #Sieve levels 4 to 20 here: finishes removing ~96% candidates total.
                print("Sieving Level: %d Time: %f" % (level, time() - s1 ))
            print("Total sieving time: ", time() - ss1 )

            candidates = [ k for k in candidates if k.bit_length() == block.nBits ] #This line requires python >= 3.10

            print("[FACTORING] height:", block.blocktemplate['height'], "nonce:", nonce, "bits:", block.nBits, "cds:", len(candidates), "/", wMAX-wMIN, "Count:", self.Count, "Found:", self.Found)
            
            #Random shuffle candidates
            random.shuffle(candidates) 

            self.kstart = time()
            check_race = 0
            for idx, n in enumerate( candidates ):
                 print("-" * 80)

                 if mine_latest_block:

                    #Check if the current block race has been won already
                    if rpc_getblockcount() + 1 != block.blocktemplate["height"]:
                        print("[LOST] Total lost time:", time() - self.START, " Seconds." )
                        return None

                 #Note: the block requires the smaller of the two prime factors to be submitted.
                 #By default, cypari2 lists the factors in ascending order so choose the first factor listed.
                 factors = factorization_handler(n)
                 self.Count += 1
                 if (len(factors) == 2):
                    fp.write("Found factors: %s\n" % factors)
                    fp.flush()
                    return self.build_pow(block,W,n,factors,nonce, idx)

            print("Runtime: ", time() - start )
            
def getParams():
    param = CParams()
    param.hashRounds = 1
    param.MillerRabinRounds = 50
    return param

gHash = ctypes.CDLL("./gHash.so").gHash
gHash.restype = uint1024

def mine():
    global SCRIPTPUBKEY
    if SCRIPTPUBKEY == None:
        SCRIPTPUBKEY = sys.argv[1].strip()
    while True:
        B = CBlock()

        print("[+] SCRIPTPUBKEY: %s" % SCRIPTPUBKEY)
        if B.mine( mine_latest_block = True, scriptPubKey = SCRIPTPUBKEY ):
            B.rpc_submitblock()
         
if __name__ == "__main__":
    mine()
