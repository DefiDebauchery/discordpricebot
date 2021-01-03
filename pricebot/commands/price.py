import discord
from discord.ext import commands

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

    @commands.command(name='lp', help='Display contents and value of LP tokens')
    async def lp_command(self, ctx: commands.Context, num_tokens=None):
        num_tokens = abs(self.bot.parse_float(num_tokens) or 1)

        values = await self.bot.get_lp_value()
        lp_price = self.bot.current_price * values[0] * 2

        token_emoji = self.bot.token['emoji'] or self.bot.token['icon'] or self.bot.token['name']
        bnb_emoji = self.bot.config['bnb_emoji']

        token_value = str(round(values[0] * num_tokens, 5))
        bnb_value = str(round(values[1] * num_tokens, 5))

        output_header = f"{format(num_tokens, '.12g')} {self.bot.token['name']}/BNB LP"
        output_body = f"{token_emoji} {token_value} + {bnb_emoji} {bnb_value}"

        embed = discord.Embed(color=0x98FB98, title=output_header, description=output_body)
        embed.set_footer(text=f"≈ ${round(lp_price * num_tokens, 4):.4f}")

        await ctx.channel.send(embed=embed)

    @commands.command(name='convert', help='Display BNB value of tokens')
    async def convert_command(self, ctx: commands.Context, num_tokens=None):
        num_tokens = abs(self.bot.parse_float(num_tokens) or 1)

        token_in_bnb = self.bot.bnb_amount / self.bot.token_amount

        token_emoji = self.bot.token['emoji'] or self.bot.token['icon'] or self.bot.token['name']
        bnb_emoji = self.bot.config['bnb_emoji']

        output_header = f"{format(round(num_tokens, 4), '.12g')} {self.bot.token['name']}"
        output_body = f"{bnb_emoji} **{round(token_in_bnb * num_tokens, 4)}**"

        usd = round(token_in_bnb * self.bot.bnb_price * num_tokens, 4)
        embed = discord.Embed(color=0x3D85C6, title=token_emoji + ' ' + output_header,
                              description=f"{output_body} _(${usd})_")

        await ctx.channel.send(embed=embed)

def setup(bot: commands.Bot):
    bot.add_cog(Prices(bot))
