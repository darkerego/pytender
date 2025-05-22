#!/usr/bin/env python3

import os
import sys

import dotenv
import web3
from web3 import AsyncWeb3
from web3.exceptions import ExtraDataLengthError
from web3.middleware import ExtraDataToPOAMiddleware

dotenv.load_dotenv()


def is_poa_chain(w3: web3.Web3):
    for x, block in enumerate([0, 'latest']):
        try:
            genesis_block = w3.eth.get_block(block)
        except ExtraDataLengthError:
            return True
        consensus_engine = genesis_block["extraData"][0:4]
        if consensus_engine in (b"\x63\x6c\x69\x71", b"\x69\x62\x66\x74"):
            return True
        else:
            if x > 0:
                break
    return False


class DotenvNotConfigured(Exception):
    pass


def get_network_env(network: str) -> str:
    endpoint = os.environ.get(f"{network}_http_endpoint")
    if endpoint is None:
        raise DotenvNotConfigured("You need to setup your `.env` file first! See docs.")
    return endpoint


def parse_network_rpc_or_env(endpoint: str = None, network: str = None) -> str | None:
    """
    Helper function that tries to find the correct RPC, not intended to be called directly.
    :param endpoint: a specific RPC. example: https://rpc.particle.network/evm-chain?chainId=1
    :param network: an evm chain name to try to get_env with: environ.get(%s_http_endpoint)
    :return: string rpc or None
    """
    if endpoint and network:
        raise ValueError("Specify either endpoint or network")
    else:
        if not endpoint and network:
            endpoint = get_network_env(network)
        elif endpoint and not network:
            assert isinstance(endpoint, str)
        elif not endpoint and not network:
            print('Warning: attempting to fallback to default env variable: `WEB3_PROVIDER_URI`', file=sys.stderr)
            endpoint = os.environ.get('WEB3_PROVIDER_URI')
    return endpoint

def setup_w3_sync(endpoint: str = None, network: str = None) -> web3.Web3 |  bool:
    """
    Set up web3 synchronously
    :param endpoint: string, rpc endpoint like https:/infura.io/whatever
    :param network: an evm chain name to try to get_env with: environ.get(%s_http_endpoint)
    :return: Web3 instance or False
    """
    endpoint = parse_network_rpc_or_env(endpoint=endpoint, network=network)
    assert endpoint is not None
    w3 = web3.Web3(web3.HTTPProvider(endpoint))
    if w3.is_connected():
        if is_poa_chain(w3):
            w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        return w3
    return False

async def async_is_poa_chain(w3: AsyncWeb3) -> bool:
    for x, block in enumerate([0, 'latest']):
        try:
            genesis_block = await w3.eth.get_block(block)
        except ExtraDataLengthError:
            return True
        else:
            extra_data = genesis_block['extraData']
            consensus_engine = extra_data[0:4]
            if consensus_engine in (b'\x63\x6c\x69\x71', b'\x69\x62\x66\x74') or len(extra_data) > 64:
                return True
            else:
                if x > 0:
                    break
    return False

async def test_needs_middleware_and_inject(w3: AsyncWeb3) -> AsyncWeb3:
    """
    If the chain that the AsyncWeb3 instance is created on requires ExtraDataMiddleware,
    inject it.

    @param w3: AsyncWeb3 instance
    @returns: AsyncWeb3 instance (with injected middleware if applicable)
    """
    if await async_is_poa_chain(w3):
        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    return w3

async def setup_w3_async(endpoint: str = None, network: str = None) -> web3.AsyncWeb3 | bool:
    """
    Set up web3 asynchronously
    :param endpoint: string, rpc endpoint like https:/infura.io/whatever
    :param network: an evm chain name to try to get_env with: environ.get(%s_http_endpoint)
    :return: AsyncWeb3 instance or False
    """
    endpoint = parse_network_rpc_or_env(endpoint=endpoint, network=network)
    assert endpoint is not None
    w3 = web3.AsyncWeb3(web3.AsyncHTTPProvider(endpoint))
    if await w3.is_connected():
        if await  async_is_poa_chain(w3):
            w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        return w3
    return False