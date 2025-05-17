#!/usr/bin/env python3

import os
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


def setup_w3_sync(network: str) -> (web3.Web3, False):
    endpoint = os.environ.get(f"{network}_http_endpoint")
    if endpoint is None:
        raise DotenvNotConfigured("You need to setup your `.env` file first! See docs.")
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

async def async_setup_w3(network: str) -> web3.AsyncWeb3 | bool:
    endpoint = os.environ.get(f"{network}_http_endpoint")
    if endpoint is None:
        raise DotenvNotConfigured("You need to setup your `.env` file first! See docs.")
    w3 = web3.AsyncWeb3(web3.AsyncHTTPProvider(endpoint))
    if await w3.is_connected():
        if await  async_is_poa_chain(w3):
            w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        return w3
    return False