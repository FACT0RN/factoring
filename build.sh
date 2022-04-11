g++ -fPIC src/gHash.cpp -shared -o gHash.so    -Wl,--whole-archive -lgmp -lcryptopp -Wl,--no-whole-archive
g++ -fPIC src/gHash.cpp -shared -o libghash.so -Wl,--whole-archive -lgmp -lcryptopp -Wl,--no-whole-archive
g++ -L.   src/gHash_test.cpp -l:libghash.so -o test_ghash
LD_LIBRARY_PATH=.  ./test_ghash 
