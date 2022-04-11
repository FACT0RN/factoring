#include "gHash.h"
#include <chrono>

int main( int argc, char* argv[]){

   //Genesis block
   CBlock block;
   block.hashPrevBlock[0] = 0;
   block.hashPrevBlock[1] = 0;
   block.hashPrevBlock[2] = 0;
   block.hashPrevBlock[3] = 0;
   block.hashMerkleRoot[0] = 13982638023556950227ULL;
   block.hashMerkleRoot[1] = 2731834534410324916ULL;
   block.hashMerkleRoot[2] = 6259368053859059585ULL;
   block.hashMerkleRoot[3] = 7654680285885345510ULL;
   
   block.nNonce   = 0;
   block.nTime    = 1644732486L;
   block.nVersion = 1;
   block.nBits    = 200;

   CParams params;
   params.hashRounds = 1;
   params.MillerRabinRounds = 32;

   using std::chrono::high_resolution_clock;
   using std::chrono::duration_cast;
   using std::chrono::duration;
   using std::chrono::milliseconds;

   auto t1 = high_resolution_clock::now();
   uint1024 N = gHash( block, params);
   auto t2 = high_resolution_clock::now();

   /* Getting number of milliseconds as a double. */
   duration<double, std::milli> ms_double = t2 - t1;

   std::cout << "  N: ";
   std::cout << std::setfill('0') << std::setw(16) << std::hex;
   std::cout << N.data[5]  << N.data[4]  << N.data[3] << N.data[2]  << N.data[1]  << N.data[0]; 
   std::cout << std::endl;
   std::cout << "Timing: " << ms_double.count() << "ms\n";
    return 0;
}
