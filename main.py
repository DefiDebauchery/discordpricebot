import sys
import importlib
from pricebot import pricebot
import yaml

bots = {}

with open('config.yaml') as cfg_file:
    cfg_data = yaml.safe_load(cfg_file)

cfg_defaults = cfg_data.pop('_config')

if len(sys.argv) < 2:
    print(f"Usage: {sys.argv[0]} <token>")
    sys.exit()

if sys.argv[1] and cfg_data.get(sys.argv[1]):
    cfg_data = {sys.argv[1]: cfg_data.get(sys.argv[1])}
else:
    raise Exception(f"Token {sys.argv[1]} does not exist in configuration!")

for cfg_name in cfg_data:
    token = ({**cfg_defaults['defaults'], **cfg_data[cfg_name]})
    token['name'] = cfg_name
    token['abi'] = pricebot.fetch_abi(token['contract'])

    if token.get('plugin'):
        try:
            module = importlib.import_module(token['plugin'])
            bots[cfg_name] = module.PriceBot(cfg_defaults, token)
        except ModuleNotFoundError:
            print(f"Token {cfg_name} has an invalid plugin configuration!")
            sys.exit()
        except AttributeError:
            print(f"The plugin for {cfg_name} must be named PriceBot!")
            sys.exit()
    else:
        bots[cfg_name] = pricebot.PriceBot(cfg_defaults, token)

    bots[cfg_name].exec()
