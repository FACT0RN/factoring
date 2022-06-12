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
docker run -d -e SCRIPTPUBKEY="avalidscriptpubkey" --network host factoring python3.10 FACTOR.py 
```

I'd recommend to run as many container as you have physical cores mines one. So, if you have 4 cores, run 3 containers by executing step 2 three times.


Happy factoring!

Note: there are a few sophiscated software implemntations for factoring. For advanced users, you can look into YAFU, ECM-GMP and CADO-NFS. I can not entertain requests to set them up for mining as they take a long time to set up and configure to mine efficiently. Creating a Dockerfile for it has proved difficult, if you are able to find one please submit it. I would be willing to do this for a fee as a percentage of mined coins, but even then, it would have to wait until I have time for it.
