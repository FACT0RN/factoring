#!/bin/sh
set -x
while true
do
  RPC_USER=rpcuser RPC_PASS=verylongrpcpasswordpassword SCRIPTPUBKEY=0014ea0f3f167fd2740cc68dfd38e17368bedf2b2b4a python3 FACTOR.py
done
