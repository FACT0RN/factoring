# Factoring
Mining code for the FACT0RN blockchain. For the binaries and instructions on how to run a node see [FACT0RN](https://github.com/FACT0RN/FACT0RN). To run the miner you will need Docker. 

You will need the scriptPubKey from an address in your wallet. For instructions on how to get a wallet, 
an address in your wallet and get the scriptPubKey for that address see the instructions on [FACT0RN](https://github.com/FACT0RN/FACT0RN).

These instructions are for the case where you are mining on the same machine where you have a node running:

1. From the parent folder of this repo, build the image:
```
docker build -t factoring .
```

2. Now, to run a container do this:

```
docker run -d -e SCRIPTPUBKEY="ValidScriptPubKey" -e RPC_USER="Your node's rpc username" -e RPC_PASS="Your node rpc's password" --network host test_factoring  bash -c "python3.10 FACTOR.py"
```

I'd recommend to run as many container as you have physical cores mines one. So, if you have 4 cores, run 3 containers by executing step 2 three times.


Happy factoring!

Note: There are a few sophiscated software implemntations for factoring. Currently, we use YAFU by default. For advanced users, you can look into YAFU, ECM-GMP and CADO-NFS. A setup using CADO-NFS is welcomed. If you create one, please let us know.
