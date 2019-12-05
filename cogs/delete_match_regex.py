import logging
import discord
from discord.ext import commands
import helpers
import re


class DeleteMatchRegEx(commands.Cog):
    def __init__(self, bot: commands.Bot, config: helpers.Config, log: logging.Logger):
        self.bot = bot
        self.config = config
        self.log = log
        self.log.info("Loaded Cog DeleteMatchRegEx")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author != self.bot.user:
            for channel in self.config.delete_match_regex:
                if message.channel.id == channel["delete_channel_id"]:
                    if not re.match(channel["regex_match_for_no_delete"], message.content, flags=re.IGNORECASE):
                        helpers.log_message_deletes([message], f"DeleteMatchRegEx {message.channel.name} {channel['regex_match_for_no_delete']}", self.log)
                        await message.delete()
                        await message.author.send("Your message was deleted! Please only use this channel to list lobbies!\n"
                                                  "Use the format described in the channel to make sure your message doesn't get deleted!")
