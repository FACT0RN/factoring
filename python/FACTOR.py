import base64
import json
import struct
import random
import sys
import struct
import gmpy2 as gmp
import os
from math import floor, ceil
from gmpy2 import mpz,mpq,mpfr,mpc
from gmpy2 import is_square, isqrt, sqrt, log2, gcd, is_prime, next_prime
import subprocess
from time import time
import multiprocessing
from lib.blockchain import *

#Attibution note: the Bitcoin RPC components here are taken
#                 from publicly available sources and are not
#                 my own original code.

SCRIPTPUBKEY = os.environ.get("SCRIPTPUBKEY") 

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

Count = 0

def mine():
    global SCRIPTPUBKEY
    if SCRIPTPUBKEY == None:
        SCRIPTPUBKEY = sys.argv[1].strip()
        
    os.system("mkdir -p logs")
    pid = os.getpid()
    fplogs = open("logs/factoring_%d.log" % pid,"a")     
   
    while True:
        B = CBlock()
        B.fplogs = fplogs
        print("[+] SCRIPTPUBKEY: %s" % SCRIPTPUBKEY)
        if B.mine( mine_latest_block = True, scriptPubKey = SCRIPTPUBKEY ):
            B.rpc_submitblock()
    fplogs.close()
    
if __name__ == "__main__":
    mine()
