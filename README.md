# discordpricebot
A Discord Bot for displaying Token Prices on Binance Smart Chain

### About
This bot will interface with both Discord and the BSC Network to continually keep a log of token prices.

Note that this will only report the mid-price; buying and selling the tokens will be lower/higher than the listed price.

### Configuration
See `config.yaml.example`. The token ticker is the parent key of the configuration.

The web3 module requires all addresses to be [checksummed](https://coincodex.com/article/2078/ethereum-address-checksum-explained/); you can get the proper address from [BSCScan](https://bscscan.com/).

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
`pip3 install requirements.txt`

You can run all configured tokens simply by `python3 main.py`, or pass a token argument to run individual instances (good for testing), such as `python3 main.py CAKE`.

### Contributing
I need all the help I can get. PRs welcome.

### TODO
- Error handling (web3 and discord)
- Better configuration (single entrypoint file referencing external configuration)
- Recording historical movements in status message
- Configurable status messages (e.g. comparing CRED price to THUGS value)