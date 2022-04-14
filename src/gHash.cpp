#include "gHash.h"

extern "C" uint1024 gHash( const CBlock block, const CParams params)
{
    //Get the required data for this block
    uint64_t nNonce              = block.nNonce;
    uint32_t nTime               = block.nTime;
    int32_t  nVersion            = block.nVersion;
    uint16_t nBits               = block.nBits;

    using namespace CryptoPP;
   
    //Place data as raw bytes into the password and salt for Scrypt:
    /////////////////////////////////////////////////
    // pass = hashPrevBlock + hashMerkle + nNonce  //
    // salt = version       + nBits      + nTime   //
    /////////////////////////////////////////////////
    byte pass[ 256/8 + 256/8 + 64/8 ] = { (byte) 0 };
    byte salt[  32/8 +  16/8 + 32/8 ] = { (byte) 0 };

    //SALT: Copy version into the first 4 bytes of the salt.
    memcpy( salt, &nVersion, sizeof(nVersion) );
    
    //SALT: Copy nBits into the next 2 bytes
    int runningLen = sizeof(nVersion);
    memcpy( &salt[runningLen], &nBits, sizeof(nBits) );

    //SALT: Copy nTime into the next 4 bytes
    runningLen += sizeof(nBits);
    memcpy( &salt[runningLen], &nTime, sizeof(nTime) );

    //PASS: Copy Previous Block Hash into the first 32 bytes
    memcpy( pass, block.hashPrevBlock, sizeof(block.hashPrevBlock) );

    //PASS: Copy Merkle Root hash into next 32 bytes
    runningLen = sizeof(block.hashPrevBlock);
    memcpy( &pass[runningLen], block.hashMerkleRoot, sizeof(block.hashMerkleRoot) );

    //PASS: Copy nNonce
    runningLen += sizeof(block.hashMerkleRoot) ;
    memcpy( &pass[runningLen], &nNonce, sizeof(nNonce) );

    ////////////////////////////////////////////////////////////////////////////////
    //                                Scrypt parameters                           //
    ////////////////////////////////////////////////////////////////////////////////
    //                                                                            //
    //  N                  = Iterations count (Affects memory and CPU Usage).     //
    //  r                  = block size ( affects memory and CPU usage).          //
    //  p                  = Parallelism factor. (Number of threads).             //
    //  pass               = Input password.                                      //
    //  salt               = securely-generated random bytes.                     //
    //  derived-key-length = how many bytes to generate as output. Defaults to 32.//
    //                                                                            //
    // For reference, Litecoin has N=1024, r=1, p=1.                              //
    ////////////////////////////////////////////////////////////////////////////////
    Scrypt scrypt;
    word64 N = 1ULL << 12;
    word64 r = 1ULL << 1;
    word64 p = 1ULL; 
    SecByteBlock derived(256);

    //Scrypt Hash to 2048-bits hash. 
    scrypt.DeriveKey(derived, derived.size(), pass, sizeof(pass), salt, sizeof(salt), N, r, p);

    //Consensus parameters
    int roundsTotal = params.hashRounds;

    //Additional hashes we will need
    SHA3_512 sHash;

    //Prepare GMP objects
    mpz_t prime_mpz, starting_number_mpz, a_mpz, a_inverse_mpz;
    mpz_init(prime_mpz);
    mpz_init(starting_number_mpz);
    mpz_init(a_mpz);
    mpz_init(a_inverse_mpz);

    for(int round =0; round < roundsTotal; round++ ){

        ///////////////////////////////////////////////////////////////
        //      Memory Expensive Scrypt: 1MB required.              //
	///////////////////////////////////////////////////////////////
	scrypt.DeriveKey(        derived,  //Final hash
                          derived.size(),  //Final hash number of bytes
             (const byte*)derived.data(),  //Input hash
                          derived.size(),  //Input hash number of bytes 
                                    salt,  //Salt
                            sizeof(salt),  //Salt bytes
                                       N,  //Number of rounds
                                       r,  //Sequential Read Sisze
                                       p   //Parallelizable iterations
        );

	///////////////////////////////////////////////////////////////
	//   Add different types of hashes to the core.              //
	///////////////////////////////////////////////////////////////
        //Count the bits in previous hash.
        uint64_t pcnt_half1 = popcnt(      derived.data(), 128 );
        uint64_t pcnt_half2 = popcnt( &derived.data()[128], 128 );

        //Hash the first 1024-bits of the 2048-bits hash.
        if( pcnt_half1 % 2 == 0 ){
            BLAKE2b bHash;
            bHash.Update((const byte*)derived.data(), 128 );
            bHash.Final((byte*)derived.data());
	}else{
            SHA3_512 bHash;
            bHash.Update((const byte*)derived.data(), 128 );
            bHash.Final((byte*)derived.data());
	}

        //Hash the second 1024-bits of the 2048-bits hash.
        if( pcnt_half2 % 2 == 0 ){
            BLAKE2b bHash;
            bHash.Update((const byte*)(&derived.data()[128]), 128 );
            bHash.Final((byte*)(&derived.data()[128]) );
        } else {
            SHA3_512 bHash;
            bHash.Update((const byte*)(&derived.data()[128]), 128 );
            bHash.Final((byte*)(&derived.data()[128]) );
	}

        //////////////////////////////////////////////////////////////
        // Perform expensive math opertions plus simple hashing     //
        //////////////////////////////////////////////////////////////
        //Use the current hash to compute grunt work.
        mpz_import( starting_number_mpz, 32, -1, 8, 0, 0, derived.data() ); // -> M = 2048-hash
        mpz_sqrt( starting_number_mpz, starting_number_mpz);                // - \ a = floor( M^(1/2) )
        mpz_set(                a_mpz, starting_number_mpz);                // - /
        mpz_sqrt( starting_number_mpz, starting_number_mpz);                // - \ p = floor( a^(1/2) )
        mpz_nextprime(      prime_mpz, starting_number_mpz);                // - /

	//Compute a^(-1) Mod p
	mpz_invert( a_inverse_mpz, a_mpz, prime_mpz);

	//Xor into current hash digest.
	size_t words = 0;
        uint64_t data[32] = {0};
        uint64_t *hDigest = (uint64_t *) derived.data();	
        mpz_export( data, &words , -1, 8, 0, 0, a_inverse_mpz );
	for(int jj=0; jj < 32; jj++)  hDigest[jj] ^= data[jj]; 

        //Check that at most 2048-bits were written
	//Assume 64-bit limbs.
	assert( words <= 32);

        //Compute the population count of a_inverse
	const int32_t irounds   = popcnt( data , sizeof(data)  ) & 0x7f;
           
	//Branch away
	for( int jj=0; jj < irounds; jj++){    	
            const int32_t br = popcnt( derived.data(), sizeof(derived.data())  );

	    //Power mod
	    mpz_powm_ui(a_inverse_mpz, a_inverse_mpz, irounds, prime_mpz  );

            //Get the data out of gmp
            mpz_export( data, &words , -1, 8, 0, 0, a_inverse_mpz );
	    assert( words <= 32 );

	    for(int jj=0; jj < 32; jj++)  hDigest[jj] ^= data[jj]; 

            if( br % 3 == 0 )
	    {
                SHA3_512 bHash;
                bHash.Update((const byte*)derived.data(), 128 );
                bHash.Final(       (byte*)derived.data()      );
	    } else if ( br % 3 == 2)
	    {
               BLAKE2b sHash;
               sHash.Update((const byte*)(&derived.data()[128]), 128 );
               sHash.Final(       (byte*)(&derived.data()[192])      );
            } else {
               Whirlpool wHash;
	       wHash.Update((const byte*)(derived.data()), 256);
               wHash.Final((byte*)(&derived.data()[112])  );
	    }
        }

    }
    
    //Compute how many bytes to copy
    int32_t allBytes = nBits/8;
    int32_t remBytes = nBits % 8;

    //Make sure to stay within 2048-bits.
    // NOTE: In the distant future this will have to be updated
    //       when nBITS starts to get close to 1024-bits.
    assert( allBytes + 1 <= 128);

    //Copy exactly the number of bytes that contains exactly the low nBits bits.
    uint1024 w;
    memset(w.data, 0, 128);

    memcpy( w.data, derived.begin(), std::min( 128, allBytes + 1) );
    
    //Trim off any bits from the Most Significant byte.
    ((uint8_t*)w.data)[allBytes] = ((uint8_t*)w.data)[allBytes] & ( (1 << remBytes) - 1 );

    //Set the nBits-bit to one.
    if( remBytes == 0){
        ((uint8_t*)w.data)[allBytes-1] = ((uint8_t*)w.data)[allBytes - 1] | 128;
    } else {
        ((uint8_t*)w.data)[allBytes] = ((uint8_t*)w.data)[allBytes] | ( 1 << (remBytes-1) );
    }

    mpz_clear(prime_mpz);
    mpz_clear(starting_number_mpz);
    mpz_clear(a_mpz);
    mpz_clear(a_inverse_mpz);

    return w;
}


int main( int argc, char *argv[])
{	
	return 0;
}

