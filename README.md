# Factoring
Mining code for the FACT0RN blockchain. For the binaries and instructions on how to run a node see [FACT0RN](https://github.com/FACT0RN/FACT0RN). To run the miner you will need python 3, a few python packages and setting some enrionmental variables. 

If you have conda you will need the following:

```
conda install -c conda-forge cypari2 
conda install -c anaconda numpy 
conda install -c conda-forge gmpy2 
conda install -c conda-forge sympy 
conda install -c conda-forge base58 
```

You will need the scriptPubKey from an address in your wallet. For instructions on how to get a wallet, 
an address in your wallet and get the scriptPubKey for that address see the instructions on [FACT0RN](https://github.com/FACT0RN/FACT0RN).

Once you have that you will need to remember the username and password you used to start your FACT0RN node. The environmental variables you will need to set are:


```
RPC_USER=< username you used to start your node >
RPC_PASS=< password you used to start your node >
SCRIPTPUBKEY=< the scriptPubKey for an address in your wallet > 
```

You use export to set them for your session, or you can do the following:

```
RPC_USER=rpcuser RPC_PASS=verylongrpcpasswordpassword SCRIPTPUBKEY=avalidscriptpubkey python FACTOR.py
```

To mine FACT0RN a function called gHash is needed. Run the ``build.sh`` script in the top folder of the repo to build the binary that has gHash. 

These instructions are for when you are mining on the same machine that you are running your node. 

Happy factoring!
