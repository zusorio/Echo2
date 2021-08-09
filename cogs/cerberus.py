import logging
import re
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

    def get_guild_config(self, guild_id: int):
        matching_guilds = [guild for guild in self.config.cerberus if guild["guild_id"] == guild_id]
        if matching_guilds:
            return matching_guilds[0]
        else:
            return False

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        self.log.info(f"Account {member.name}#{member.discriminator} created at {member.created_at}")

        guild_config = self.get_guild_config(member.guild.id)
        log_channel = self.bot.get_channel(guild_config["log_channel_id"])
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

        elif datetime.utcnow() - member.created_at < timedelta(seconds=guild_config["warn_max_time_seconds"]):
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
        if message.author.bot:
            return
        self.recent_messages.appendleft(message)
        similar_message_count = len(set([recent_message.channel.id for recent_message in self.recent_messages if
                                         recent_message.author.id == message.author.id and recent_message.content == message.content]))

        is_mod = message.author.guild_permissions.manage_messages
        if similar_message_count > 5:
            account_age_text = humanfriendly.format_timespan(datetime.utcnow() - message.author.created_at)

            guild_config = self.get_guild_config(message.guild.id)
            log_channel = self.bot.get_channel(guild_config["log_channel_id"])

            regex = r"\b((?:https?://)?(?:(?:www\.)?(?:[\da-z\.-]+)\.(?:[a-z]{2,6})|(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)|(?:(?:[0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,7}:|(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,5}(?::[0-9a-fA-F]{1,4}){1,2}|(?:[0-9a-fA-F]{1,4}:){1,4}(?::[0-9a-fA-F]{1,4}){1,3}|(?:[0-9a-fA-F]{1,4}:){1,3}(?::[0-9a-fA-F]{1,4}){1,4}|(?:[0-9a-fA-F]{1,4}:){1,2}(?::[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:(?:(?::[0-9a-fA-F]{1,4}){1,6})|:(?:(?::[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(?::[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(?:ffff(?::0{1,4}){0,1}:){0,1}(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])|(?:[0-9a-fA-F]{1,4}:){1,4}:(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])))(?::[0-9]{1,4}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])?(?:/[\w\.-]*)*/?)\b"
            urls_in_message = re.findall(regex, message.content)
            if len(urls_in_message) > 0 and not is_mod:
                await message.author.ban(reason="Automatic Ban by Cerberus")
                embed = discord.Embed(
                    title=f"Automatically banned Spam Bot {message.author.name}#{message.author.discriminator}",
                    description=message.content, color=0xFE0B00)
            else:
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
