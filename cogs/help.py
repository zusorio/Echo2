import logging
import discord
from discord.ext import commands
import helpers


class Help(commands.Cog):
    def __init__(self, bot: commands.Bot, config: helpers.Config, log: logging.Logger):
        self.bot = bot
        self.config = config
        self.log = log
        self.log.info("Loaded Cog Help")

    @commands.command()
    async def help(self, ctx: commands.Context):
        embed = discord.Embed(title="Echo Help", color=0x358bbb)
        embed.add_field(name=f"{self.config.bot_prefix}balance",
                        value=f"`{self.config.bot_prefix}balance` view your PUG Point balance\n"
                              f"`{self.config.bot_prefix}balance @SomeUser` view @SomeUsers PUG Point balance",
                        inline=False
                        )
        embed.add_field(name=f"{self.config.bot_prefix}leaderboard",
                        value=f"`{self.config.bot_prefix}leaderboard` view the PUG Point leaderboard\n",
                        inline=False)
        embed.add_field(name=f"{self.config.bot_prefix}gp - For Staff only",
                        value=f"`{self.config.bot_prefix}gp @SomeUser` give SomeUser one PUG Point\n"
                              f"`{self.config.bot_prefix}gp @SomeUser 5` give SomeUser 5 PUG Points",
                        inline=False)
        embed.add_field(name=f"{self.config.bot_prefix}ping - For PUG Veterans only",
                        value=f"`{self.config.bot_prefix}ping eu Need some more people for PUGs`\nPing the Unofficial role in the EU channel with your message\n",
                        inline=False)
        await ctx.send(embed=embed)
