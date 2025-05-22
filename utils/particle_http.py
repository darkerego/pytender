import asyncio
import os

import dotenv
import httpx
from web3 import AsyncWeb3
from web3.eth import AsyncEth
from web3.middleware import ExtraDataToPOAMiddleware
from web3.providers import AsyncBaseProvider
from web3.types import RPCEndpoint
from utils.initialize_w3 import async_is_poa_chain

PARTICLE_SUPPORTED = [(1, 'ethereum'), (43114, 'avalanche'), (56, 'bsc'), (137, 'polygon'), (10, 'optimism'),
                      (42161, 'arbitrum'), (42170, 'nova'), (8453, 'base'), (534352, 'scroll'), (324, 'zksync'),
                      (1101, 'polygonzkevm'), (1284, 'moonbeam'), (1285, 'moonriver'), (1313161554, 'aurora'),
                      (1030, 'confluxespace'), (22776, 'mapprotocol'), (728126428, 'tron'), (42220, 'celo'),
                      (25, 'cronos'), (250, 'fantom'), (100, 'gnosis'), (1666600000, 'harmony'), (128, 'heco'),
                      (321, 'kcc'), (8217, 'klaytn'), (1088, 'metis'), (42262, 'oasisemerald'), (66, 'okc'),
                      (321, 'platon'), (108, 'thundercore')]




class CustomParticleProvider(AsyncBaseProvider):
    def __init__(self, chain_id: int = 1):
        super().__init__()
        dotenv.load_dotenv()
        self.project_id = os.environ.get('PARTICLE_PROJECT_ID')
        self.project_client_key = os.environ.get('PARTICLE_CLIENT_KEY')
        self.chain_id = chain_id
        self.base_url = "https://rpc.particle.network/evm-chain"
        self.headers = {'Content-Type': 'application/json'}
        self.auth = httpx.BasicAuth(self.project_id, self.project_client_key)
        self.client = httpx.AsyncClient(auth=self.auth, headers=self.headers, timeout=60,
                                        limits=httpx.Limits(max_connections=100))

    async def make_request(self, method: RPCEndpoint, params):
        # Prepare the request payload, ensuring chainId could be included in params if necessary
        payload = {
            'jsonrpc': '2.0',
            'chainId': self.chain_id,
            'method': method,
            'params': params,
            'id': 1  # Static ID for simplicity, could be made dynamic
        }
        # Send the request
        response = await self.client.post(self.base_url, json=payload)
        response.raise_for_status()  # Ensure to check for HTTP errors
        return response.json()


def find_cid(name: str):
    for net in PARTICLE_SUPPORTED:
        cid = net[0]
        chain_name = net[1]
        if name.lower() == chain_name:
            return cid
    return 0


async def create_w3(cid: int = None, chain_name: str = None) -> AsyncWeb3:
    if cid is None:
        assert chain_name is not None
        cid = find_cid(chain_name)
        assert cid != 0

    provider = CustomParticleProvider(chain_id=cid)
    w3 = AsyncWeb3(provider, modules={'eth': (AsyncEth,)})
    if await async_is_poa_chain(w3):
        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    return w3


# Usage example
async def test_main(cid: int):
    w3 = await create_w3(cid)
    block_number = await w3.eth.block_number
    base_fee = await w3.eth.gas_price
    print(f"Current Block Number: {block_number}")
    print(f'Current Base Fee: {base_fee}')


