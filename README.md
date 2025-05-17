# PyTender

## tenderly lib & cli tool in python

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

python -m tenderly --help
usage: __main__.py [-h] [--debug] [--chain-id CHAIN_ID] [--config CONFIG] {create,get,fund,clock} ...

positional arguments:
  {create,get,fund,clock}
    create              Create a new virtual forked nnetwork
    get                 Get all or a specific vnet
    clock               Change various evm global attributes such as block time

options:
  -h, --help            show this help message and exit
  --debug               Enable intensely verbose debug data.
  --chain-id CHAIN_ID
  --config CONFIG       Config located in ./configs with the vnet data


</pre>


- create a new vnet:  
    - ` python -m tenderly --chain-id 1 create UniqueNetName`
- get a vnet (i.e. the last created) : 
  - `python -m tenderly get --latest`
- 