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
docker run -ti -e SCRIPTPUBKEY="ValidScriptPubKey" -e RPC_USER="Your node's rpc username" -e RPC_PASS="Your node rpc's password" -e YAFU_THREADS=max_core_count_minus_one -e YAFU_LATHREADS=max_core_count_minus_one -e MSIEVE_BIN="/tmp/ggnfs-bin/" --network host factorn_mining  bash -c "python3.10 FACTOR.py"
```

I'd recommend to run one container. Use as many threads as you have cores, minus one so the OS has on core to do normal system stuff. If you run htop you will see how many cores you have.


Happy factoring!

Note: There are a few sophiscated software implemntations for factoring. Currently, we use YAFU by default. For advanced users, you can look into YAFU, ECM-GMP and CADO-NFS. A setup using CADO-NFS is welcomed. If you create one, please let us know.

# Contact

Website: https://fact0rn.io <br>
Whitepaper: https://fact0rn.io/FACT0RN_whitepaper.pdf <br>
Coinbase: https://blog.coinbase.com/fact0rn-blockchain-integer-factorization-as-proof-of-work-pow-bc48c6f2100b <br>
E-mail: fact0rn@pm.me <br>
Discord: https://discord.gg/tE2BNpgmtH <br>
Twitter: https://twitter.com/FACT0RN <br>
Reddit: https://www.reddit.com/r/FACT0RN/
