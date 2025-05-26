# PyTender



Copyright [darkergo](https://github.com/darkerego)   
<p>DarkerEgo, 2025, Licensed under MIT</p>

## tenderly lib & cli tool in python

#### Changelog

- May 25th, 2025
  - Notice: there's a bug somewhere, for some reason if you try 
   to create a new vnet by calling as a module `python3 -m tenderly` 
   it may fail, in that case, it does however work fine calling directly, 
   not sure why, trying to debug that, for now, that's a workaround 
  

- May 23rd, 2025
  - Add changelog
  - created `TenderlyArgs` class, a wrapper around `argparse.Namespace`, 
    - intended to be used non-interactively, i.e. when using this as a library,
    rather than a cli tool.
  - Started writing some basic tests
    - also intended to serve as examples of how one may implement 
    this as a library for another program.
  - add logic for handling initial start, when there is no saved 
  vnet config, which warns the user and prints a helpful message 
  explaining how to set that up. 


#### Installation

- Edit .env.empty
    - get api keys from particle
    - get api keys from tenderly
    - save as .env
  
- run the installation:

<pre>
git clone https://github.com/darkerego/pytender
cd pytender
virtualenv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python3 setup.py build
python3 setup.py install
</pre>




#### Usage


<pre>

$ python3 -m tenderly --help
usage: __main__.py [-h] [--debug] [--chain-id CHAIN_ID] [--config CONFIG] {create,get,fund,clock,test} ...

positional arguments:
  {create,get,fund,clock,test}
    create              Create a new virtual forked nnetwork
    get                 Get all or a specific vnet
    clock               Change various evm global attributes such as block time
    test                Test a vnet with AsyncWeb3. Perform a few view only calls.

options:
  -h, --help            show this help message and exit
  --debug               Enable intensely verbose debug data.
  --chain-id CHAIN_ID, --cid CHAIN_ID
  --config CONFIG       Config located in ./configs with the vnet data

</pre>


- create a new vnet:  
    - ` python -m tenderly --chain-id 1 create UniqueNetName`
- get a vnet (i.e. the last created) : 
  - `python -m tenderly get --latest`
- fund an account with 10 Ether:
  - `python -m tenderly --config last.json fund 0x1234567890123456789012345678901234567890` 10
- Test the virtual network via web3.AsyncWeb3:
  - notice: automatically created and available via `TenderlyVnet.w3_tenderly` helper function  
  - `python -m tenderly --config last.json test`
    - returns the current block number as an integer. 
#### TODO:
 - add the rest of tenderly's API functions
 - better state override handling 
 - state over-ride via config files maybe? 
 - package on PyPi so we can install with pip directly
 - anything else? reach out and let me know! 