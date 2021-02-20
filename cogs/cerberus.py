import logging
from datetime import timedelta, datetime

import discord
import humanfriendly
from discord.ext import commands

import helpers


class Cerberus(commands.Cog):
    """
    Warn of newly created accounts
    """

    def __init__(self, bot: commands.Bot, config: helpers.Config, log: logging.Logger):
        self.bot = bot
        self.config = config
        self.log = log
        self.log.info("Loaded Cog Cerberus")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        self.log.info(f"Account {member.name}#{member.discriminator} created at {member.created_at}")
        if datetime.utcnow() - member.created_at < timedelta(seconds=self.config.cerberus["warn_max_time_seconds"]):
            account_age_text = humanfriendly.format_timespan(datetime.utcnow() - member.created_at)
            log_channel = self.bot.get_channel(self.config.cerberus["log_channel_id"])
            embed = discord.Embed(title=f"Found suspicious new Member {member.name}#{member.discriminator}",
                                  description=f"Their account was created {account_age_text} ago")
            embed.set_author(name=member.display_name, icon_url=member.avatar_url)
            embed.set_footer(text="Cerberus by Echo",
                             icon_url="https://cdn.discordapp.com/app-icons/581523092363411493/9f85d39eb6321ad12b2d13396c4595f5.png?size=256")
            await log_channel.send(embed=embed)
