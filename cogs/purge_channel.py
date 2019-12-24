import logging
import discord
from discord.ext import commands
import helpers


class PurgeChannel(commands.Cog):
    def __init__(self, bot: commands.Bot, config: helpers.Config, log: logging.Logger):
        self.bot = bot
        self.config = config
        self.log = log
        self.log.info("Loaded Cog PurgeChannel")

    @commands.command()
    async def purge_channel(self, ctx: commands.Context, channel_alias: str):
        for channel in self.config.purge_channel:
            if ctx.channel.id == channel["command_channel_id"] and channel_alias == channel["purge_channel_alias"]:
                # Get the channel to purge
                discord_channel: discord.TextChannel
                discord_channel = discord.utils.get(self.bot.get_all_channels(), id=channel["purge_channel_id"])
                # Used to check that the message isn't protected
                delete_allowed = lambda message: message.id not in channel["purge_ignore_messages"]
                # Purge the messages that aren't protected
                deleted_messages = await discord_channel.purge(check=delete_allowed)
                helpers.log_message_deletes(deleted_messages, f"ChannelPurge {channel_alias}", self.log)
                if deleted_messages:
                    await ctx.send(f"Done! Deleted {len(deleted_messages)} {'message' if len(deleted_messages) == 1 else 'messages'}")
