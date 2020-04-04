import logging
import discord
from discord.ext import commands
import helpers
import re


class DeleteMatchRegEx(commands.Cog):
    """
    Deletes messages if they don't match a RegEx. Used to keep lobby channel on topic
    """
    def __init__(self, bot: commands.Bot, config: helpers.Config, log: logging.Logger):
        self.bot = bot
        self.config = config
        self.log = log
        self.log.info("Loaded Cog DeleteMatchRegEx")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Message is not from self or another bot
        if message.author != self.bot.user and message.author.bot is not True:
            # Go over all configured channels
            for channel in self.config.delete_match_regex:
                if message.channel.id == channel["delete_channel_id"]:
                    # If the message doesn't contain our protect RegEx delete the message
                    if not re.search(channel["protect_regex"], message.content, flags=re.IGNORECASE):
                        helpers.log_message_deletes([message], f"DeleteMatchRegEx {message.channel.name} {channel['protect_regex']}", self.log)
                        await message.delete()
                        await message.author.send("Your message was deleted! Please only use this channel to list lobbies!\n"
                                                  "Use the format described in the channel to make sure your message doesn't get deleted!")
