import json
import os
import discord
from discord.ext import tasks
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

class PriceBot(discord.Client):
    web3 = Web3(Web3.HTTPProvider('https://bsc-dataseed2.binance.org'))
    contracts = {}
    config = {}
    current_price = 0
    nickname = ''
    bnb_amount = 0
    bnb_price = 0
    token_amount = 0

    # Static BSC contract addresses
    address = {
        'bnb' : '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c',
        'busd': '0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56'
    }

    def __init__(self, config, token):
        super().__init__()
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
        total_supply = self.contracts['lp'].functions.totalSupply().call()
        return [self.token_amount / total_supply, self.bnb_amount / total_supply]

    async def on_guild_join(self, guild):
        guild.me.edit(nick=self.nickname)

    async def on_ready(self):
        loop = tasks.loop(seconds=self.token['refresh_rate'])(self.update_price)
        loop.add_exception_type(discord.errors.HTTPException)
        loop.start()

    async def update_price(self):
        await self.change_presence(activity=discord.Game(name=self.generate_presence()))
        self.current_price = self.get_token_price()

        for guild in self.guilds:
            await guild.me.edit(nick=self.generate_nickname())

    async def on_message(self, message: discord.Message):
        if not self.is_ready() or message.author.bot or not self.user.mentioned_in(message):
            return

        args = message.content.split()
        if args[0] != f"<@!{self.user.id}>" or len(args) < 2:
            return

        command = args[1]
        if command == 'lp':
            await self.lp_command(message)
        elif command == 'convert':
            await self.convert_command(message)

    async def lp_command(self, message: discord.Message):
        args = message.content.split()
        multi = 1

        if len(args) >= 3:
            num_tokens = self.parse_float(args[2])
            if num_tokens:
                multi = num_tokens

        values = await self.get_lp_value()
        lp_price = self.current_price * values[0] * 2

        msg = f"{multi:g} LP Token{' is' if multi == 1 else 's are'} worth ≈${round(lp_price * multi, 4)}\n" \
              f"{round(values[0] * multi, 5)} {self.token['icon']} + {round(values[1] * multi, 5)} BNB"

        await message.channel.send(msg)

    async def convert_command(self, message: discord.Message):
        args = message.content.split()
        multi = 1

        if len(args) >= 3:
            num = self.parse_float(args[2])
            if num:
                multi = num

        token_in_bnb = self.bnb_amount / self.token_amount

        msg = f"{multi:g} {self.token['icon']} is {round(token_in_bnb * multi, 4)} BNB (${round(token_in_bnb * self.bnb_price * multi, 4)})"
        await message.channel.send(msg)

    @staticmethod
    def parse_float(val):
        try:
            val = float(val)
        except ValueError:
            val = None

        return val

    def exec(self):
        self.run(self.token['apikey'])
