import pricebot

discord_api_key = ''
refresh_rate = 15  # How frequently prices are retrieved, in seconds. 15 is every 5 BSC blocks.

token = {
    'contract'   : '0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82',
    'name'       : 'CAKE',
    'icon'       : '🥞',
    'lp_contract': '0xA527a61703D82139F8a06Bc30097cC9CAA2df5A6',
    'busd_lp'    : '0x1B96B92314C44b159149f7E0303511fB2Fc4774f'
}

token['abi'] = pricebot.fetch_abi(token['contract'])
# Or load local copy with json.load(open('tokenabi.json', 'r'))

config = {
    'refresh_rate': refresh_rate,
    'discord_api_key': discord_api_key,
    'token': token
}
bot = pricebot.PriceBot(config)
bot.run()
