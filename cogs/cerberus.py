import logging
from collections import deque
from datetime import timedelta, datetime

import discord
import humanfriendly
from discord.ext import commands

import helpers


class Cerberus(commands.Cog):
    """
    Handle new accounts
    """

    def __init__(self, bot: commands.Bot, config: helpers.Config, log: logging.Logger):
        self.bot = bot
        self.config = config
        self.log = log
        self.log.info("Loaded Cog Cerberus")
        self.recent_messages = deque([], maxlen=100)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        self.log.info(f"Account {member.name}#{member.discriminator} created at {member.created_at}")

        log_channel = self.bot.get_channel(self.config.cerberus["log_channel_id"])
        account_age_text = humanfriendly.format_timespan(datetime.utcnow() - member.created_at)

        # Handle spam bots
        if "h0nde" in member.name.lower() and "twitter" in member.name.lower():
            await member.ban(reason="Automatic Ban by Cerberus")
            embed = discord.Embed(title=f"Automatically banned Spam Bot {member.name}#{member.discriminator}",
                                  description=f"Their account was created {account_age_text} ago", color=0xFE0B00)
            embed.add_field(name="ID", value=member.id, inline=True)
            embed.set_thumbnail(url=member.avatar_url)
            embed.set_footer(text="Cerberus by Echo",
                             icon_url="https://cdn.discordapp.com/app-icons/581523092363411493/9f85d39eb6321ad12b2d13396c4595f5.png?size=256")
            await log_channel.send(embed=embed)

        elif datetime.utcnow() - member.created_at < timedelta(seconds=self.config.cerberus["warn_max_time_seconds"]):
            embed = discord.Embed(title=f"Found suspicious new Member {member.name}#{member.discriminator}",
                                  description=f"Their account was created {account_age_text} ago", color=0x358BBB)
            embed.add_field(name="ID", value=member.id, inline=True)
            embed.add_field(name="Clickable", value=member.mention, inline=True)
            embed.set_thumbnail(url=member.avatar_url)
            embed.set_footer(text="Cerberus by Echo",
                             icon_url="https://cdn.discordapp.com/app-icons/581523092363411493/9f85d39eb6321ad12b2d13396c4595f5.png?size=256")
            await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        self.recent_messages.appendleft(message)
        similar_message_count = len(set([recent_message.channel.id for recent_message in self.recent_messages if
                                         recent_message.author.id == message.author.id and recent_message.content == message.content]))
        if similar_message_count > 5:
            account_age_text = humanfriendly.format_timespan(datetime.utcnow() - message.author.created_at)
            log_channel = self.bot.get_channel(self.config.cerberus["log_channel_id"])
            embed = discord.Embed(
                title=f"Found duplicate messages by {message.author.name}#{message.author.discriminator}",
                description=message.content, color=0xFE0B00)
            embed.add_field(name="ID", value=message.author.id, inline=True)
            embed.add_field(name="Account created", value=f"{account_age_text} ago", inline=True)
            embed.add_field(name="Message Link", value=message.jump_url, inline=False)
            embed.set_thumbnail(url=message.author.avatar_url)
            embed.set_footer(text="Cerberus by Echo",
                             icon_url="https://cdn.discordapp.com/app-icons/581523092363411493/9f85d39eb6321ad12b2d13396c4595f5.png?size=256")
            await log_channel.send(embed=embed)
