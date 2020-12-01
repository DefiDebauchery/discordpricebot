import json
import discord
from discord.ext import tasks
from urllib.request import urlopen, Request
from web3 import Web3

# Static BSC contract addresses
address = {
    'bnb' : '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c',
    'busd': '0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56'
}

web3 = Web3(Web3.HTTPProvider('https://bsc-dataseed2.binance.org'))

def fetch_abi(contract):
    # TODO: Error handling
    url = 'https://api.bscscan.com/api?module=contract&action=getabi&address=' + contract
    abi_response = urlopen(Request(url, headers={'User-Agent': 'Mozilla'})).read().decode('utf8')
    return json.loads(abi_response)['result']

class PriceBot(discord.Client):
    contracts = {}
    config = {}

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.token = config['token']

        self.contracts['bnb'] = web3.eth.contract(address=address['bnb'], abi=self.token['abi'])
        self.contracts['busd'] = web3.eth.contract(address=address['busd'], abi=self.token['abi'])
        self.contracts['token'] = web3.eth.contract(address=self.token['contract'], abi=self.token['abi'])

    def get_bnb_price(self, lp):
        bnb_amount = self.contracts['bnb'].functions.balanceOf(lp).call()
        busd_amount = self.contracts['busd'].functions.balanceOf(lp).call()

        return busd_amount / bnb_amount

    def get_price(self, contract, native_lp, bnb_lp):
        bnb_amount = self.contracts['bnb'].functions.balanceOf(native_lp).call()
        token_amount = contract.functions.balanceOf(native_lp).call()

        bnb_price = self.get_bnb_price(bnb_lp)

        return (bnb_amount / token_amount) * bnb_price

    def get_token_price(self):
        return round(self.get_price(self.contracts['token'], self.token['lp_contract'], self.token['busd_lp']), 4)

    def generate_presence(self):
        return self.token['name'] + ' price'

    async def on_ready(self):
        await self.change_presence(activity=discord.Game(self.generate_presence()))
        tasks.loop(seconds=self.config['refresh_rate'])(self.update_price).start()

    async def update_price(self):
        final_price = str(self.get_token_price())
        for guild in self.guilds:
            await guild.me.edit(nick=self.token['icon'] + ' $' + final_price)

    def run(self):
        super().run(self.config['discord_api_key'])
