# discordpricebot
A Discord Bot for displaying Token Prices on Binance Smart Chain

### About
This bot will interface with both Discord and the BSC Network to continually keep a log of token prices.

Note that this will only report the mid-price; buying and selling the tokens will be lower/higher than the listed price.

### Configuration
```
token = {
    'contract'   : '0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82',
    'name'       : 'CAKE',
    'icon'       : '🥞',
    'lp_contract': '0xA527a61703D82139F8a06Bc30097cC9CAA2df5A6',
    'busd_lp'    : '0x1B96B92314C44b159149f7E0303511fB2Fc4774f'
}

token['abi'] = pricebot.fetch_abi(token['contract'])
```

The `contract` is the Token itself.  
The LP variables refer to the AMM you want to use as your price reference:  
`lp_contract` is the BNB/{Token} LP Pair address  
`busd_lp` is the BNB/BUSD pair for the AMM for USD price calculation.

The `name` and `icon` simply give flavor to the bot. The icon can be omitted.

The web3 module requires all addresses to be [checksummed](https://coincodex.com/article/2078/ethereum-address-checksum-explained/); you can get the proper address from BSCScan.

### Authorizing Discord User

- Visit https://discord.com/developers/applications and create 'New Application'.
- Set a worthy name
- On the page that follows, set the account name and save. Then click Bot
- Create a Bot account and Save. Click 'Copy' on the Token; this is the API Key you use in the bot script
- Visit the OAuth2 tab. Under Scopes, select 'bot'
- The resulting URL is what you (or anyone) use to add your bot instance to a server.

A single bot instance can be added to multiple servers; the bot's nickname (the price) will be updated on all registered servers.

### Installation and Execution
This assumes you already have python3 and pip3 installed on your system.

Install the pre-requisites:  
`pip3 install discord web3 rusty-rlp`

For each token bot you want to run (one Discord bot per token), simply copy the entry script, then run it. For long-term execution on *nix environments, consider using `nohup`:  
`nohup python3 cake.py &`

### Contributing
I need all the help I can get. PRs welcome.

### TODO
- Error handling (web3 and discord)
- Better configuration (single entrypoint file referencing external configuration)
- Recording historical movements in status message
- Configurable status messages (e.g. comparing CRED price to THUGS value)