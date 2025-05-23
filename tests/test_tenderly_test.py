import asyncio

from tenderly.tenderly import tenderly_main
from tenderly.tenderly import TenderlyArgs


if __name__ == '__main__':
    _args = TenderlyArgs(True, 8453, 'last.json', kwlist={"command": "test"})
    api = tenderly_main(True, _args)
    coro = api.test_virtual_net_web3()
    ret = asyncio.run(api.main(coro, _args.config))
    assert isinstance(ret, int)
    print('Current block number for chain with id %s: %s' % (_args.chain_id, ret))