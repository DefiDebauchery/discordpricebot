import json
import os, sys

import discord
from discord.ext import tasks, commands
from pathlib import Path
from urllib.request import urlopen, Request
from web3 import Web3

def fetch_abi(contract):
    if not os.path.exists('contracts'):
        os.mkdir('./contracts')

    filename = f'contracts/{contract}.json'
    if os.path.exists(filename):
        with open(filename, 'r') as abi_file:
            abi = abi_file.read()
    else:
        # TODO: Error handling
        url = 'https://api.bscscan.com/api?module=contract&action=getabi&address=' + contract
        abi_response = urlopen(Request(url, headers={'User-Agent': 'Mozilla'})).read().decode('utf8')
        abi = json.loads(abi_response)['result']

        with open(filename, 'w') as abi_file:
            abi_file.write(abi)

    return json.loads(abi)

def list_cogs(directory):
    basedir = (os.path.basename(os.path.dirname(__file__)))
    #return ['pricebot.commands.price', 'pricebot.commands.admin', 'pricebot.commands.owner']
    return (f"{basedir}.{directory}.{f.rstrip('.py')}" for f in os.listdir(basedir + '/' + directory) if f.endswith('.py'))

class PriceBot(commands.Bot):
    web3 = Web3(Web3.HTTPProvider('https://bsc-dataseed2.binance.org'))
    contracts = {}
    config = {}
    current_price = 0
    nickname = ''
    bnb_amount = 0
    bnb_price = 0
    token_amount = 0
    total_supply = 0

    # Static BSC contract addresses
    address = {
        'bnb' : '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c',
        'busd': '0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56'
    }

    def __init__(self, config, token):
        super().__init__(command_prefix=commands.when_mentioned, help_command=None, case_insensitive=True)
        self.config = config
        self.token = token
        self.amm = config['amm'][token['from']]

        if not config['amm'].get(token['from']):
            raise Exception(f"{token['name']}'s AMM {token['from']} does not exist!")

        self.contracts['bnb'] = self.web3.eth.contract(address=self.address['bnb'], abi=self.token['abi'])
        self.contracts['busd'] = self.web3.eth.contract(address=self.address['busd'], abi=self.token['abi'])
        self.contracts['token'] = self.web3.eth.contract(address=self.token['contract'], abi=self.token['abi'])
        self.contracts['lp'] = self.web3.eth.contract(address=self.token['lp'], abi=fetch_abi(self.token['lp']))

    def get_bnb_price(self, lp):
        bnb_amount = self.contracts['bnb'].functions.balanceOf(lp).call()
        busd_amount = self.contracts['busd'].functions.balanceOf(lp).call()

        self.bnb_price = busd_amount / bnb_amount

        return self.bnb_price

    def get_price(self, token_contract, native_lp, bnb_lp):
        self.bnb_amount = self.contracts['bnb'].functions.balanceOf(native_lp).call()
        self.token_amount = token_contract.functions.balanceOf(native_lp).call()

        bnb_price = self.get_bnb_price(bnb_lp)

        try:
            final_price = (self.bnb_amount / self.token_amount) * bnb_price
        except ZeroDivisionError:
            final_price = 0

        return final_price

    def get_token_price(self):
        return round(self.get_price(self.contracts['token'], self.token['lp'], self.amm), 4)

    def generate_presence(self):
        return self.token['name'] + ' price'

    def generate_nickname(self):
        return f"{self.token['icon']} ${str(self.current_price)} ({round(self.bnb_amount / self.token_amount, 4)})"

    async def get_lp_value(self):
        self.total_supply = self.contracts['lp'].functions.totalSupply().call()
        return [self.token_amount / self.total_supply, self.bnb_amount / self.total_supply]

    async def on_guild_join(self, guild):
        await guild.me.edit(nick=self.nickname)

    async def on_message(self, message):
        server_restriction = self.config.get('restrict_to', {}).get(message.guild.id)
        if not server_restriction or await self.is_owner(message.author):
            return await self.process_commands(message)

        if message.channel.id not in server_restriction:
            if message.channel.permissions_for(message.guild.me).manage_messages:
                await message.message.delete()
            return

        await self.process_commands(message)

    async def on_ready(self):
        restrictions = self.config.get('restrict_to', {})
        all_channels = self.get_all_channels()
        for guild_id, channels in restrictions.items():
            for i, channel in enumerate(channels):
                if self.parse_int(channel):
                    channels[i] = self.get_channel(channel)
                else:
                    channels[i] = discord.utils.get(all_channels, guild__id=guild_id, name=channel)

        await self.update_price()
        loop = tasks.loop(seconds=self.config['refresh_rate'])(self.update_price)
        loop.add_exception_type(discord.errors.HTTPException)
        loop.start()

    async def update_price(self):
        await self.change_presence(activity=discord.Game(name=self.generate_presence()))
        self.current_price = self.get_token_price()

        for guild in self.guilds:
            await guild.me.edit(nick=self.generate_nickname())

    @staticmethod
    def parse_int(val):
        try:
            val = int(val)
        except ValueError:
            val = None

        return val

    @staticmethod
    def parse_float(val):
        if val is None:
            return val

        try:
            val = float(val)
        except ValueError:
            val = None

        return val

    def exec(self):
        for cog in list_cogs('commands'):
            try:
                if self.token.get('command_override'):
                    override = self.token.get('command_override')
                    cog = override.get(cog, cog)

                self.load_extension(cog)
            except Exception as e:
                print(f'Failed to load extension {cog}.', e)

        self.run(self.token['apikey'])
