//Big Integer Arithmetic
#include <gmp.h>

//Blake2b, Scrypt and SHA3-512
#include "cryptopp/cryptlib.h"
#include "cryptopp/sha3.h"
#include "cryptopp/whrlpool.h"
#include "cryptopp/scrypt.h"
#include "cryptopp/secblock.h"
#include "cryptopp/blake2.h"
#include "cryptopp/hex.h"
#include "cryptopp/files.h"

//Fancy popcount implementation
#include "libpopcnt.h"

#include <cassert>
#include <iomanip>

typedef struct CBlock {
   uint64_t  nP1[16];
   uint64_t  hashPrevBlock[4];
   uint64_t  hashMerkleRoot[4];
   uint64_t  nNonce;
   int64_t   wOffset;
   int32_t   nVersion;
   uint32_t  nTime;
   uint16_t  nBits;
} CBlock;

typedef struct CParams {
   uint32_t hashRounds;
   uint32_t MillerRabinRounds;
} CParams;

typedef struct uint1024 {
   uint64_t data[16];
} uint1024;

extern "C" uint1024 gHash( const CBlock block, const CParams params);
