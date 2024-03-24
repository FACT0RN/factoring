################################################################################
# Bitcoin Daemon JSON-HTTP RPC
################################################################################
import json
import urllib
import base64
import random
import os

RPC_PORT     = os.environ.get("RPC_PORT", "8332")
RPC_URL      = os.environ.get("RPC_URL", "http://127.0.0.1"  ) + ":" + str(RPC_PORT)
RPC_USER     = os.environ.get("RPC_USER", "rpcuser")
RPC_PASS     = os.environ.get("RPC_PASS", "rpcpass")

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

def rpc_getblockhash(height):
    return rpc( "getblockhash", [height] )

def rpc_getblock( Hash ):
    return rpc( "getblock", [Hash, 2] )

def block_who( height ):
    bhash = rpc_getblockhash(height)
    block = rpc_getblock(bhash)
    wallet = block['tx'][0]['vout'][0]['scriptPubKey']['address']
    mtime = block['mediantime']

    return mtime

def get_blocktime( n ):
    TOP = rpc_getblockcount()
    BLOCK_TIME = [0] * n
    k = 0


    for height in range(TOP - n, TOP ):
        BLOCK_TIME[ k ] = block_who(height)
        k += 1

    return BLOCK_TIME
