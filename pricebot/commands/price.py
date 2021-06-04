import math
from datetime import datetime

import discord
from discord.ext import tasks, commands
from decimal import Decimal, DecimalException
from pricebot.commands.models import prices

class Prices(commands.Cog, command_attrs=dict(hidden=True)):
    current_ath = None

    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db

        prices.Base.metadata.create_all(self.bot.dbengine)
        query = self.db.query(prices.PriceATH).filter(prices.PriceATH.token == self.bot.token['contract'])
        if result := query.first():
            self.current_ath = result

    @commands.Cog.listener()
    async def on_ready(self):
        await self.update_price()

        self.bot.priceloop = tasks.loop(seconds=self.bot.config['refresh_rate'])(self.update_price)
        self.bot.priceloop.add_exception_type(discord.errors.HTTPException)
        self.bot.priceloop.start()

    async def update_price(self):
        try:
            self.bot.current_price = self.bot.get_token_price()
        except Exception:
            # Ignore issues with blockchain timeouts, but don't update anything
            return

        for guild in self.bot.guilds:
            await guild.me.edit(nick=self.bot.generate_nickname())

        if self.current_ath:
            if self.bot.current_price > self.current_ath.price:
                try:
                    self.current_ath.price = self.bot.current_price
                    self.current_ath.timestamp = datetime.utcnow()

                    self.db.update(self.current_ath)
                    self.db.commit()
                    return await self.bot.change_presence(activity=discord.Game(name='ATH Hit!'))
                except Exception:
                    pass
        else:
            ath = prices.PriceATH(token=self.bot.token['contract'], price=self.bot.current_price)
            self.db.add(ath)
            self.db.commit()

            self.current_ath = ath

        presence = self.bot.generate_presence()
        if presence:
            await self.bot.change_presence(activity=discord.Game(name=presence))

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound) or isinstance(error, commands.CheckFailure):
            pass
        else:
            raise error

    async def cog_check(self, ctx: commands.Context):
        if isinstance(ctx.channel, discord.channel.DMChannel):
            return True
        return await self.bot.check_restrictions(ctx)

    @commands.command(help='Display contents and value of LP tokens')
    async def lp(self, ctx: commands.Context, num_tokens=None):
        num_tokens = abs(self.bot.parse_decimal(num_tokens) or 1)

        with ctx.typing():
            total_supply = self.bot.total_supply
            values = [Decimal(self.bot.token_amount / total_supply), Decimal(self.bot.bnb_amount / total_supply)]

            bnb_emoji = self.bot.config['bnb_emoji']

            token_value = str(round(values[0] * num_tokens, 5))
            bnb_value = str(round(values[1] * num_tokens, 5))

            output_header = f"{format(num_tokens, '.12g')} {self.bot.token['name']}/BNB LP"
            output_body = f"{self.bot.icon_value(token_value)} + {bnb_emoji} {bnb_value}"

        embed = discord.Embed(color=0x98FB98, title=output_header, description=output_body)

        footer_text = f"≈ ${round(self.bot.lp_price * num_tokens, 4):.4f}"
        amm_info = self.bot.get_amm()
        if amm_info.get('name'):
            footer_text += f" | via {amm_info.get('name')}"

        embed.set_footer(text=footer_text)

        await ctx.channel.send(embed=embed)

    @commands.command(help='Display BNB value of tokens')
    async def convert(self, ctx: commands.Context, num_tokens=None):
        num_tokens = self.bot.parse_decimal(num_tokens) or Decimal(1)

        total_price = num_tokens * self.bot.current_price
        price_in_bnb = total_price / self.bot.bnb_price

        token_emoji = self.bot.icon_value()
        bnb_emoji = self.bot.config['bnb_emoji']

        output_header = f"{format(float(num_tokens.quantize(self.bot.display_precision)), '.12g')} {self.bot.token['name']}"
        output_body = f"{bnb_emoji} **{Decimal(price_in_bnb).quantize(self.bot.display_precision)}**"

        usd = Decimal(price_in_bnb * self.bot.bnb_price).quantize(self.bot.display_precision)
        embed = discord.Embed(color=0x3D85C6, title=token_emoji + ' ' + output_header,
                              description=f"{output_body} _(${usd})_")

        amm_info = self.bot.get_amm()
        if amm_info.get('name'):
            embed.set_footer(text=f"via {amm_info.get('name')}")

        await ctx.channel.send(embed=embed)

    @commands.command()
    async def ath(self, ctx: commands.Context):
        token_emoji = self.bot.icon_value()
        if not self.current_ath:
            return

        time = self.current_ath.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')

        output_body = f"The highest price for {self.bot.token['name']} was **${self.current_ath.price}**"

        embed = discord.Embed(color=discord.Color.green(), title=token_emoji + ' All Time High', description=output_body)

        amm_info = self.bot.get_amm()
        if amm_info.get('name'):
            embed.set_footer(text=f"Recorded {time} via {amm_info.get('name')}")

        await ctx.channel.send(embed=embed)

def setup(bot: commands.Bot):
    bot.add_cog(Prices(bot))
