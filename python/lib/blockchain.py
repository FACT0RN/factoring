################################################################################
# Bitcoin Core Wrappers
################################################################################
from lib.number_theory import *
from lib.ctypes import *
from lib.rpc import *
from lib.repr import *
from lib.transaction import *
from lib.factordb_connector import *
import os
import struct
import random
import ctypes
import statistics
import subprocess

SIEVE_MAX_LEVEL = os.environ.get("SIEVE_MAX_LEVEL")
if SIEVE_MAX_LEVEL == None:
  SIEVE_MAX_LEVEL = 27
else:
  SIEVE_MAX_LEVEL = int(SIEVE_MAX_LEVEL)

BASE_PRIMORIAL = 2*3*5*7*11*13
SIEVER = prime_levels_load(4, SIEVE_MAX_LEVEL + 1)


def getParams():
    param = CParams()
    param.hashRounds = 1
    param.MillerRabinRounds = 50
    return param

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

    def __init__(self):
        global BASE_PRIMORIAL, SIEVER, SIEVE_MAX_LEVEL
        self.fplogs = None
        self.base_primorial = BASE_PRIMORIAL
        self.siever = SIEVER
        self.sieve_max_level = SIEVE_MAX_LEVEL
   
    def build_pow(self, block, W, n, factors, nonce, idx):
        pdiff = abs(factors[0].bit_length() - factors[1].bit_length())
        print("Factors bit diff: %d" % pdiff)
        if ( factors[0].bit_length() == ( block.nBits//2 + (block.nBits&1)) ):
          print( " {:> 5d} {:> 5d} {:> 5d} {:> 5d} {:> 3.3f} Seconds".format( idx, len(factors), factors[0].bit_length(), block.nBits//2, time()-self.kstart ), flush=True )
          #Update values for the found block
          block.nP1     = IntToUint1024(min(factors))
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
          
          if self.fplogs != None:
              self.fplogs.write("Found block_hash: %s\n" % str(block_hash.hex()))
              self.fplogs.flush()
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
        global primorial_base, siever, SIEVE_MAX_LEVEL
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
        coinbase_tx['data'] = tx_make_coinbase(coinbase_script, scriptPubKey, block.blocktemplate['coinbasevalue'], block.blocktemplate['height'], block.blocktemplate['default_witness_commitment'])
        coinbase_tx['txid'] = tx_compute_hash(coinbase_tx['data'])

        #Add transaction to our block
        block.blocktemplate['transactions'].insert(0, coinbase_tx)
        
        # Recompute the merkle root
        block.blocktemplate['merkleroot'] = tx_compute_merkle_root([tx['txid'] for tx in block.blocktemplate['transactions']])
        merkleRoot = uint256()
        merkleRoot = (ctypes.c_uint64 * 4)(*hashToArray( block.blocktemplate["merkleroot"] if mine_latest_block else "6a3ae329ed61aee656ddbe14d8b2878125e96d0900ac0bb4c20c4f3300fb68d3")) 
        block.hashMerkleRoot = merkleRoot

        #Iterate through a small set of random nonces
        #Probability of finding a good semiprime is extremely high
        Seeds = [ random.randint(0,1<<64) for i in range(10000)] if mine_latest_block else list(range(10000))
        BLOCK_TIME = get_blocktime( 50 )
        T = [t - s for s, t in zip(BLOCK_TIME, BLOCK_TIME[1:])]
        avg = sum(T)/len(T)
        std = statistics.stdev(T)
        timeout = avg + 0*std

        print("Recent Block Solving Stats ( Last ", str(50), " Blocks )")
        print("    Avg Solve Time:", avg , " Seconds. ", avg/60, " Mins." )
        print("Standard Deviation:", std , " Seconds. ", std/60, " Mins." )
        print("      Yafu Timeout:","avg + 0*std ~ ", timeout, "Seconds or ", timeout//60, "minutes", timeout%60, "Seconds."  )

	

        for nonce in Seeds:
            start = time()
            total_time = 0

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
            total_cand_count = wMAX - wMIN

            #Candidates for admissible semiprime
            lstart = time()
            candidates = [ a for a in range( wMIN, wMAX) if gcd( a, self.base_primorial ) == 1 and not is_prime(a)  ]
            print("Sieving Levels: 1,2,3,4 Time: %f Filtered: %d" % ( time() - lstart, total_cand_count - len(candidates) ) )

            #Sieve up to level 26 by default.
            ss1 = time()
            for level in range(5,self.sieve_max_level+1):
                s1 = time()
                before = len(candidates)
                candidates = [ n for n in candidates if gcd(self.siever[level], n ) == 1  ] #Sieve levels 4 to 20 here: finishes removing ~96% candidates total.
                after = len(candidates)
                print("Sieving Level: %d Time: %f Filtered: %d" % (level, time() - s1, before - after) )
            print("Total sieving time: %f Sieved: %d of %d  (%f%%)" % ( time() - ss1, total_cand_count - len(candidates), total_cand_count, 100*(total_cand_count - len(candidates))/total_cand_count )  )
 
            candidates = [ k for k in candidates if k.bit_length() == block.nBits ] #This line requires python >= 3.10

            print("[FACTORING] height:", block.blocktemplate['height'], "nonce:", nonce, "bits:", block.nBits, "cds:", len(candidates), "/", wMAX-wMIN, "Count:", self.Count, "Found:", self.Found)
            
            #Random shuffle candidates
            random.shuffle(candidates) 

            self.kstart = time()
            check_race = 0
            for idx, n in enumerate( candidates ):
                 print("-" * 50, idx, "of", len(candidates), 50*"-")

                 if mine_latest_block:

                    #Check if the current block race has been won already
                    if rpc_getblockcount() + 1 != block.blocktemplate["height"]:
                        parse = subprocess.run( "pkill yafu", capture_output=True, shell=True )
                        print("[LOST] Total lost time:", time() - self.START, " Seconds." )
                        return None

                 #Note: the block requires the smaller of the two prime factors to be submitted.
                 #By default, cypari2 lists the factors in ascending order so choose the first factor listed.
                 factors = factorization_handler(n, timeout )
                 factors = [ int(a.split("=")[1]) for a in factors ]

                 self.Count += 1
                 if (len(factors) == 2):
                    if ( factors[0].bit_length() ==  ( block.nBits//2 + (block.nBits&1))  ):
                        pPrime = is_prime(factors[0])
                        qPrime = is_prime(factors[1])
                        if (  (pPrime and qPrime) == True  ):
                            if self.fplogs != None:
                                self.fplogs.write("Found factors: %s\n" % factors)
                                self.fplogs.flush()
                            return self.build_pow(block,W,n,factors,nonce, idx)


            print("Runtime: ", time() - start )
