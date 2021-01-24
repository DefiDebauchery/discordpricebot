import discord
from discord.ext import commands

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.bot.config.get('restrict_to'):
            self.bot.config['restrict_to'] = {}

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound) or isinstance(error, commands.CheckFailure):
            pass
        else:
            raise error

    @commands.group(name='restriction')
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    async def restriction(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            pass

    @restriction.command(name='list')
    async def list_restrictions(self, ctx: commands.Context):
        restrictions = self.bot.config['restrict_to'].get(ctx.guild.id)
        if restrictions:
            response = "Restricted to the following channels: "
            response += ' '.join([channel.mention for channel in restrictions])
            return await ctx.channel.send(response)

        await ctx.channel.send('No restrictions on this server')

    @restriction.command(name='add')
    async def add_restriction(self, ctx: commands.Context, channel: discord.TextChannel):
        restrictions = self.bot.config['restrict_to'].get(ctx.guild.id)
        if not restrictions:
            restrictions = self.bot.config['restrict_to'][ctx.guild.id] = []

        restrictions.append(channel)

        await ctx.channel.send(f'Restricted to {channel.name}')

    @restriction.command(name='remove')
    async def remove_restriction(self, ctx: commands.Context, channel: discord.TextChannel):
        restrictions = self.bot.config['restrict_to'].get(ctx.guild.id)
        if restrictions:
            await ctx.channel.send(f"Removed restriction for {channel.name}")

        await ctx.channel.send("I don't have a restriction to that channel!")

    @restriction.command(name='clear')
    async def clear_restrictions(self, ctx:commands.Context):
        self.bot.config['restrict_to'][ctx.guild.id] = []
        await ctx.channel.send(f'Clearing all restrictions.')

def setup(bot: commands.Bot):
    bot.add_cog(Admin(bot))
