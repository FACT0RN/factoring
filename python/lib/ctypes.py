################################################################################
# CTypes and utility functions
################################################################################
import ctypes

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

gHash = ctypes.CDLL("../libs/gHash.so").gHash
gHash.restype = uint1024

