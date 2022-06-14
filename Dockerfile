FROM ubuntu:22.04

RUN apt update && apt install -y  \ 
                  git             \ 
                  vim             \
                  gcc             \
                  g++             \ 
                  cmake           \
                  libgmp-dev      \
                  libcrypto++8    \
                  libcrypto++-dev \ 
                  python3.10      \
                  python3-pip     \
                  pari-gp         \
                  libpari-dev     

RUN pip install sympy gmpy2 numpy base58 cypari2 factordb-python

WORKDIR /tmp/factoring

COPY src src 
COPY FACTOR.py FACTOR.py
COPY build.sh build.sh

RUN ./build.sh

CMD bash
