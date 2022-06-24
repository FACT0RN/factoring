#!/bin/sh
set -x
export RPC_USER="rpcuser"
export RPC_PASS="verylongrpcpasswordpassword"
export SCRIPTPUBKEY="Your_SCRIPTPUBKEY_goes_here"
while true
do
   python3 FACTOR.py
done
