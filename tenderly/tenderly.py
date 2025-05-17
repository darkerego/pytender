import argparse
import asyncio
import os
import pprint
import time

import dotenv
import httpx
import uvloop
import web3
from eth_typing import ChecksumAddress
from eth_utils import to_checksum_address
from typing_extensions import NamedTuple

from lib import particle_http
from utils.json_helper import JsonHelper

TENDERLY_USER = os.environ.get('TENDERLY_USER')
TENDERLY_PROJECT = os.environ.get('TENDERLY_PROJECT')
TENDERLY_ACCESS_KEY = os.environ.get('TENDERLY_ACCESS_KEY')


class VirtualNetworkId(str):
    pass


class VirtualNetwork(NamedTuple):
    """
    vnet_id,
    forked_net_id,
    slug,
    admin_rpc,
    public_rpc
    """
    vnet_id: str
    forked_net_id: int
    slug: str
    admin_rpc: str
    public_rpc: str

    def as_dict(self):
        return self._asdict()


class BadHttpStatus(Exception):
    pass


async def parse_response(resp: httpx.Response):

    # debug_data = {'http_status': f"{resp.status_code}", 'response': resp.json()}

    if resp.status_code >= 200 <400:
        return resp.json()
    raise BadHttpStatus(resp.status_code)


class TenderlyVnet:
    def __init__(self,
                 account: str = TENDERLY_USER,
                 project: str = TENDERLY_PROJECT,
                 access_key: str = TENDERLY_ACCESS_KEY,
                 cid: int = 1,
                 debug: bool = False):
        self.account = account
        self.project = project
        self.access_key = access_key
        self.cid = cid
        self.debug = debug
        self._w3: web3.AsyncWeb3 | None = None
        self.session = httpx.AsyncClient(headers=self.headers)
        self.a_initialized = False
        self.current_vnet: VirtualNetwork | None = None
        self.vnet_list: dict[str, VirtualNetwork]
        self.json_helper = JsonHelper
        self.http_id_counter: int = 1

    async def __ainit__(self):
        try:
            os.mkdir('./configs')
        except FileExistsError:
            pass

        if not self.a_initialized:
            self._w3 = await particle_http.create_w3(self.cid)
            print('[+] Connected to: %s' % await self._w3.eth.chain_id)
            print('[+] Debug: %s ' % self.debug)

    @property
    def headers(self):
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Access-Key": self.access_key
        }

    @property
    def w3(self):
        return self._w3

    @property
    def base_url(self):
        return f"https://api.tenderly.co/api/v1/account/{self.account}/project/{self.project}/vnets"

    async def post(self, url: str, payload: dict) -> dict | list:
        response = await self.session.post(url, json=payload, headers=self.headers)
        self.http_id_counter += 1
        return await parse_response(response)

    async def get(self, url: str) -> dict | list:
        response = await self.session.get(url, headers=self.headers)
        self.http_id_counter += 1
        return await parse_response(response)

    async def increase_evm_time(self, seconds: int):
        payload = {
            "jsonrpc": "2.0",
            "method": "evm_increaseTime",
            "params": [hex(seconds)],
            "id": f"{self.http_id_counter}"
        }
        return await self.post(self.current_vnet.admin_rpc, payload)

    async def set_eth_balance(self, addresses: list[ChecksumAddress], new_balance: int):
        payload = {
            "jsonrpc": "2.0",
            "method": "tenderly_setBalance",
            "params": [addresses,
                       hex(new_balance)],
            "id": f"{self.http_id_counter}"
        }
        return await self.post(self.current_vnet.admin_rpc, payload)

    async def set_erc20_balance(self, address: ChecksumAddress, token: ChecksumAddress, new_balance: int):
        payload = {
            "jsonrpc": "2.0",
            "method": "tenderly_setErc20Balance",
            "params": [
                token,  # token
                address,  # wallet
                hex(new_balance)  # wei value
            ],
            "id": self.http_id_counter
        }
        return await self.post(self.current_vnet.admin_rpc, payload)

    async def set_balance(self, token_address: ChecksumAddress | None, account_address: ChecksumAddress,
                          new_balance: float) -> dict:
        if not token_address:
            return await self.set_eth_balance([account_address], int(new_balance) * 10 ** 18)
        token = self.w3.eth.contract(to_checksum_address(token_address),
                                     abi=self.json_helper.load_json('data/EIP20.json'))
        decimals = token.functions.decimals().call()
        return await self.set_erc20_balance(account_address, token_address, int(new_balance * 10 ** decimals))

    async def send_transaction(self, vnet_id: str, from_address: ChecksumAddress, to_address: ChecksumAddress,
                               gas: int, gas_price: int, ether_value: int, call_data: str,
                               state_overrides: dict = None, block_overrides: dict = None):
        """

        :param vnet_id:
        :param from_address:
        :param to_address:
        :param gas:
        :param gas_price:
        :param ether_value:
        :param call_data:
        :param state_overrides: {"0x3F41a1CFd3C8B8d9c162dE0f42307a0095A6e5DF": {"balance": "0x124125"}} | nonce, code, stateDiff
        :param block_overrides: {"number": "0x124214","timestamp": "0x124124"}
        :return:
        """
        url = self.base_url + '/' + vnet_id + '/transactions'
        if not state_overrides:
            state_overrides = {}
        if not block_overrides:
            block_overrides = {}
        payload = {
            "callArgs": {
                "from": from_address,
                "to": to_address,
                "gas": hex(gas),
                "gasPrice": hex(gas_price),
                "value": hex(ether_value),
                "data": call_data
            },
            "stateOverrides": state_overrides,
            "blockOverrides": block_overrides
        }

        response = await self.session.post(url, json=payload, headers=self.headers)
        return response.json()

    def load_and_set_current_vnet(self, conf_file: str):
        vnet = self.load_vnet_config(conf_file)
        self.set_working_vnet(vnet)

    def load_vnet_config(self, conf_file: str) -> VirtualNetwork:
        assert os.path.exists(conf_file)
        return VirtualNetwork(**self.json_helper.load_json(conf_file))

    def save_vnet_config(self, vnet: VirtualNetwork):
        self.json_helper.dump_json(vnet.as_dict(), 'configs/%s_%s.json' % (vnet.slug, time.time()))

    async def get_vnet(self, vnet_id: str):
        url = self.base_url + '/' + vnet_id
        response = await self.session.get(url, headers=self.headers)
        return response.json()

    async def get_all_vnet(self):
        response = await self.session.get(self.base_url)
        return response.json()

    def set_working_vnet(self, vnet: VirtualNetwork):
        self.current_vnet = vnet
        print('[+] Current virtual network: %s' % vnet.vnet_id, 'Params: ')
        pprint.pprint(vnet.as_dict())

    async def get_vnet_by_index(self, index: int = 0) -> VirtualNetwork:
        vnet_lst = await self.get_all_vnet()
        if self.debug:
            for x, n in enumerate(vnet_lst):
                if x == index:
                    pprint.pprint(n)
        last_vnet = vnet_lst[index]
        vnet = VirtualNetwork(last_vnet.get('id'), last_vnet.get('fork_config').get('network_id'),
                              last_vnet.get('slug'),
                              last_vnet.get('rpcs')[0].get('url'), last_vnet.get('rpcs')[2].get('url'))
        return vnet

    async def get_latest_vnet(self, save: bool = False, as_dict: bool = False) -> VirtualNetwork | dict:
        vnet = await self.get_vnet_by_index(0)
        if save:
            self.json_helper.dump_json(vnet.as_dict(), 'configs/%s.json' % vnet.slug)
        if as_dict:
            return vnet.as_dict()
        return vnet

    async def get_set_latest_vnet(self) -> VirtualNetwork:
        vnet = await self.get_latest_vnet()
        self.set_working_vnet(vnet)
        return vnet

    async def create_vnet(
            self,
            slug: str = None,
            # cid: int = 1,
            block: int = 0,
            display_name: str = None,
    ):
        await self.__ainit__()
        url = self.base_url
        if not display_name:
            display_name = f'{slug}_{self.cid}_dev_net'
        if block == 0:
            block = await self.w3.eth.get_block_number()

        payload = {
            "slug": slug,
            "display_name": display_name,
            "fork_config": {
                "network_id": self.cid,
                "block_number": hex(block)
            },
            "virtual_network_config": {"chain_config": {"chain_id": self.cid}},
            "sync_state_config": {"enabled": False},
            "explorer_page_config": {
                "enabled": False,
                "verification_visibility": "bytecode"
            }
        }
        response = await self.session.post(url, json=payload, headers=self.headers)
        return response.json()

    async def main(self, _coro: asyncio.coroutines, config: str = None):
        if config:
            self.load_and_set_current_vnet('./configs/' + config + '.json')
        await self.__ainit__()
        _ret = await _coro
        await asyncio.sleep(1)
        return _ret


class TenderlyAsyncWeb3(web3.AsyncWeb3):
   def __init__(self, w3: web3.AsyncWeb3):
       self._w3 = w3
       super().__init__()


class TenderlyWrapped(TenderlyAsyncWeb3):
    def __init__(self, *args, **kwargs):
        TenderlyAsyncWeb3.__init__(*args, **kwargs)


def cli_main():
    dotenv.load_dotenv()
    cli_args = argparse.ArgumentParser()
    cli_args.add_argument('--debug', action='store_true', help='Enable intensely verbose debug data.')
    cli_args.add_argument('--chain-id', dest='chain_id', type=int, default=1)
    cli_args.add_argument('--config', type=str, help='Config located in ./configs with the vnet data')
    subparsers = cli_args.add_subparsers(dest='command')
    create = subparsers.add_parser('create', help='Create a new virtual forked nnetwork')
    create.add_argument('slug', type=str)
    #  create.add_argument('cid', type=int, default=1)
    create.add_argument('--name', type=str, default=None)
    create.add_argument('--block', type=int, default=0)
    get_vnet = subparsers.add_parser('get', help='Get all or a specific vnet')
    get_vnet.add_argument('--id', dest='vnet_id', default=None, help='ID of specific vnet')
    get_vnet.add_argument('--latest', action='store_true', help='Get the most recently created vnet')
    get_vnet.add_argument('--save', action='store_true', help='Save the vnet to a json file')
    fund = subparsers.add_parser('fund')

    fund.add_argument('account', type=str, help='Account to top up.')
    fund.add_argument('amount', type=float, default=1, help='Float value to set to account. Auto converted'
                                                            ' to Wei')
    fund.add_argument('-t', '--token', type=str, default=None)
    evm_clock = subparsers.add_parser('clock', help='Change various evm global attributes such as block time')
    evm_clock.add_argument('evm_command', type=str, choices=['forward'])
    evm_clock.add_argument('difference', type=int)

    cli_args = cli_args.parse_args()

    # asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    asyncio.get_event_loop_policy()
    if not cli_args.debug:
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    print('[+] Event loop: ', asyncio.get_event_loop())
    api = TenderlyVnet(debug=cli_args.debug, cid=cli_args.chain_id)
    if cli_args.command == 'create':
        coro = api.create_vnet(cli_args.slug, cli_args.block, cli_args.name)
    elif cli_args.command == 'get':
        if cli_args.vnet_id:
            coro = api.get_vnet(cli_args.vnet_id)
        else:
            if cli_args.latest:
                coro = api.get_latest_vnet(cli_args.save, True)
            else:
                coro = api.get_all_vnet()
    elif cli_args.command == 'fund':

        coro = api.set_balance(cli_args.token, cli_args.account, cli_args.amount)
    elif cli_args.command == 'clock':
        if cli_args.evm_command == 'forward':
            coro = api.increase_evm_time(cli_args.difference)
        else:
            raise ValueError('Unknown evm command: %s ' % cli_args.evm_command)
    else:
        raise ValueError("Unknown command: %s" % cli_args.command)
    ret = asyncio.run(api.main(coro, config=cli_args.config))
    if ret:
        pprint.pprint(ret)
    else:
        print('[!] Failed to execute command: %s' % cli_args.command)

if __name__ == '__main__':
    cli_main()
