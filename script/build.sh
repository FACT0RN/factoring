mkdir -p libs
g++ -fPIC ./src/gHash.cpp -shared -o ./libs/gHash.so    -Wl,--whole-archive -lgmp -lcryptopp -Wl,--no-whole-archive
g++ -fPIC ./src/gHash.cpp -shared -o ./libs/libghash.so -Wl,--whole-archive -lgmp -lcryptopp -Wl,--no-whole-archive
g++ -L.   ./src/gHash_test.cpp -l:./libs/libghash.so -o test_ghash
LD_LIBRARY_PATH=./libs/  ./test_ghash 
