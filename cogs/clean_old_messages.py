import logging
import discord
from datetime import datetime, timedelta
from discord.ext import commands, tasks
import helpers


class CleanOldMessages(commands.Cog):
    """
    Deletes messages that have a certain age
    """
    def __init__(self, bot: commands.Bot, config: helpers.Config, log: logging.Logger):
        self.bot = bot
        self.config = config
        self.log = log
        self.log.info("Loaded Cog CleanOldMessages")
        self.initialize.start()

    @tasks.loop(seconds=1, count=1)
    async def initialize(self):
        # wait until bot is fully ready before starting task, otherwise it breaks
        await self.bot.wait_until_ready()
        self.clean_old_messages.start()
        self.log.info("CleanOldMessages is fully ready")

    async def delete_message(self, message: discord.Message):
        await message.delete()
        # If the message has normal content display it after deleting
        if message.content:
            self.log.warning(f"Deleted message {message.content} by {message.author.display_name} in {message.channel.name}")
        # Else the message must have an embed
        else:
            self.log.warning(f"Deleted an embed by {message.author.display_name} in {message.channel.name}")

    @tasks.loop(seconds=60)
    async def clean_old_messages(self):
        self.log.debug("cleaning")
        # Go over all channels in the config
        for channel in self.config.clean_old_messages:
            # Get them as channel object
            discord_channel: discord.TextChannel
            discord_channel = discord.utils.get(self.bot.get_all_channels(), id=channel["channel_id"])
            # Calculate how old they have to be to get deleted
            delete_minimum_age = datetime.utcnow() - timedelta(seconds=channel["delete_minimum_age_seconds"])
            # Returns true if message is not in the ignore list
            delete_allowed = lambda message: message.id not in channel["delete_ignore_messages"]
            deleted_messages = await discord_channel.purge(check=delete_allowed, before=delete_minimum_age)
            helpers.log_message_deletes(deleted_messages, "CleanOldMessages", self.log)
