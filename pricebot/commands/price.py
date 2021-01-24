import math

import discord
from discord.embeds import EmptyEmbed
from discord.ext import commands
from decimal import Decimal, DecimalException
from web3 import Web3

class Prices(commands.Cog, command_attrs=dict(hidden=True)):
    def __init__(self, bot):
        self.bot = bot

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
            values = await self.bot.get_lp_value()
            lp_price = self.bot.current_price * values[0] * 2

            bnb_emoji = self.bot.config['bnb_emoji']

            token_value = str(round(values[0] * num_tokens, 5))
            bnb_value = str(round(values[1] * num_tokens, 5))

            output_header = f"{format(num_tokens, '.12g')} {self.bot.token['name']}/BNB LP"
            output_body = f"{self.bot.icon_value(token_value)} + {bnb_emoji} {bnb_value}"

        embed = discord.Embed(color=0x98FB98, title=output_header, description=output_body)

        footer_text = f"≈ ${round(lp_price * num_tokens, 4):.4f}"
        amm_info = self.bot.get_amm()
        if amm_info.get('name'):
            footer_text += f" | via {amm_info.get('name')}"

        embed.set_footer(text=footer_text)

        await ctx.channel.send(embed=embed)

    @commands.command(help='Display BNB value of tokens')
    async def convert(self, ctx: commands.Context, num_tokens=None):
        num_tokens = self.bot.parse_decimal(num_tokens) or Decimal(1)

        token_in_bnb = self.bot.bnb_amount / self.bot.token_amount

        token_emoji = self.bot.icon_value()
        bnb_emoji = self.bot.config['bnb_emoji']

        output_header = f"{format(float(num_tokens.quantize(self.bot.display_precision)), '.12g')} {self.bot.token['name']}"
        output_body = f"{bnb_emoji} **{Decimal(token_in_bnb * num_tokens).quantize(self.bot.display_precision)}**"

        usd = Decimal(token_in_bnb * self.bot.bnb_price * num_tokens).quantize(self.bot.display_precision)
        embed = discord.Embed(color=0x3D85C6, title=token_emoji + ' ' + output_header,
                              description=f"{output_body} _(${usd})_")

        amm_info = self.bot.get_amm()
        if amm_info.get('name'):
            embed.set_footer(text=f"via {amm_info.get('name')}")

        await ctx.channel.send(embed=embed)

    @commands.command(help='Death to fractions!')
    @commands.dm_only()
    async def round(self, ctx: commands.Context, address):
        try:
            address = Web3.toChecksumAddress(address)
        except ValueError:
            return await ctx.channel.send('Please use a valid wallet address!')

        async with ctx.typing():
            i = 0
            exponent = 10 ** self.bot.token['decimals']
            token_balance = Decimal(self.bot.contracts['token'].functions.balanceOf(address).call()) / exponent
            lines = [['To Get', 'Purchase']]

            if token_balance:
                whole_number = int(token_balance)

                while whole_number > (mag := (10 ** i)):
                    i += 1
                    target_balance = math.ceil(token_balance / mag) * mag
                    lines.append([str(target_balance), str(target_balance - token_balance)])
            else:
                embed = discord.Embed(color=0xff2400, title="No Balance", description=f"This wallet has 0 {self.bot.token['icon']}")
                return await ctx.message.reply(embed=embed)

        col_widths = [max(len(s[0]) for s in lines), max(len(s[1]) for s in lines)]
        header = lines.pop(0)
        table = f"{header[0].rjust(col_widths[0])} | {header[1]}\n"
        for line in lines:
            table += f"{line[0].rjust(col_widths[0])} | {line[1].rjust(col_widths[1])}\n"

        output = f'{self.bot.icon_value(token_balance)} ```{table}```'

        embed = discord.Embed(colour=discord.Color.green(), title="Balance Rounding", description=output)
        embed.set_footer(text=f"For {address}")

        await ctx.channel.send(embed=embed)

    @commands.command(help="What's in my pocket?")
    async def balance(self, ctx: commands.Context, address):
        try:
            address = Web3.toChecksumAddress(address)
        except ValueError:
            return await ctx.channel.send('Please send a valid wallet address!')

        async with ctx.typing():
            exponent = 10 ** self.bot.token['decimals']
            token_balance = Decimal(self.bot.contracts['token'].functions.balanceOf(address).call()) / exponent

        if token_balance:
            return await self.convert(ctx, token_balance)

        embed = discord.Embed(color=0xff2400, title="No Balance", description=f"This wallet has 0 {self.bot.token['icon']}")
        await ctx.message.reply(embed=embed)

def setup(bot: commands.Bot):
    bot.add_cog(Prices(bot))
