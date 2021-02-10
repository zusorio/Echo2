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

        for region in self.config.vet_ping_unofficials:
            region_channel = self.bot.get_channel(region["command_channel_id"])
            permissions_in_region_channel = ctx.author.permissions_in(region_channel)
            if permissions_in_region_channel.read_messages and permissions_in_region_channel.send_messages:
                embed.add_field(name=f"{self.config.bot_prefix}ping - For PUG Veterans only",
                                value=f"`{self.config.bot_prefix}ping eu Need some more people for PUGs`\n"
                                      f"Ping the Unofficial role in the EU channel with your message\n",
                                inline=False)
                break

        if any([role.id for role in ctx.author.roles if role.id in self.config.pug_points["allowed_roles"]]):
            embed.add_field(name=f"{self.config.bot_prefix}gp - For Staff only",
                            value=f"`{self.config.bot_prefix}gp @SomeUser` give SomeUser one PUG Point\n"
                                  f"`{self.config.bot_prefix}gp @SomeUser 5` give SomeUser 5 PUG Points",
                            inline=False)

        for channel in self.config.purge_channel:
            purge_channel = self.bot.get_channel(channel["command_channel_id"])
            permissions_in_purge_channel = ctx.author.permissions_in(purge_channel)
            if permissions_in_purge_channel.read_messages and permissions_in_purge_channel.send_messages:
                embed.add_field(name=f"{self.config.bot_prefix}purge_channel - For PUG Veterans only",
                                value=f"`{self.config.bot_prefix}purge_channel eu` Delete all messages in eu channel except for pinned one\n"
                                      f"`{self.config.bot_prefix}purge_channel lobbies` Delete all messages in lobbies channel except for pinned one\n",
                                inline=False)
                break

        await ctx.send(embed=embed)
