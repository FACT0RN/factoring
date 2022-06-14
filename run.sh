#!/bin/sh
set -x
while true
do
  RPC_USER=rpcuser RPC_PASS=verylongrpcpasswordpassword SCRIPTPUBKEY="Your_SCRIPTPUBKEY_goes_here" python3 FACTOR.py
done
