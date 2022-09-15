# Factoring
Mining code for the FACT0RN blockchain. For the binaries and instructions on how to run a node see [FACT0RN](https://github.com/FACT0RN/FACT0RN). To run the miner you will need Docker. 

You will need the scriptPubKey from an address in your wallet. For instructions on how to get a wallet, 
an address in your wallet and get the scriptPubKey for that address see the instructions on [FACT0RN](https://github.com/FACT0RN/FACT0RN).

These instructions are for the case where you are mining on the same machine where you have a node running:

1. From the parent folder of this repo, build the image:
```
docker build -t factorn_mining .
```

2. Now, to run a container do this:

```
docker run -ti -e SCRIPTPUBKEY="ValidScriptPubKey" -e RPC_USER="Your node's rpc username" -e RPC_PASS="Your node rpc's password" -e YAFU_THREADS=4 -e YAFU_LATHREADS=4 --network host factorn_mining  bash -c "python3.10 FACTOR.py"
```

I'd recommend to run as many container as you have physical cores mines one. So, if you have 4 cores, run 3 containers by executing step 2 three times.


Happy factoring!

Note: There are a few sophiscated software implemntations for factoring. Currently, we use YAFU by default. For advanced users, you can look into YAFU, ECM-GMP and CADO-NFS. A setup using CADO-NFS is welcomed. If you create one, please let us know.

# Contact

Website: https://fact0rn.io <br>
Whitepaper: https://fact0rn.io/FACT0RN_whitepaper.pdf <br>
Coinbase: https://blog.coinbase.com/fact0rn-blockchain-integer-factorization-as-proof-of-work-pow-bc48c6f2100b <br>
E-mail: fact0rn@pm.me <br>
Discord: https://discord.gg/gG7MXxS5Fd <br>
Twitter: https://twitter.com/LionesEscanor <br>
Reddit: https://www.reddit.com/r/FACT0RN/
