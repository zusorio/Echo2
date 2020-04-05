import logging
import discord
from discord.ext import commands
import helpers
import pyowapi
import re


class WarnWrongBattletags(commands.Cog):
    """
    Warns users when their battletags are incorrect
    """

    def __init__(self, bot: commands.Bot, config: helpers.Config, log: logging.Logger):
        self.bot = bot
        self.config = config
        self.log = log
        self.log.info("Loaded Cog WarnWrongBattleTags")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author != self.bot.user:
            for channel in self.config.warn_wrong_battletags:
                # Check if the message is in one of the bnet channels
                if message.channel.id == channel["channel_id"]:
                    # Extract battletags
                    battletags = re.findall("(?:\\S*)#(?:[0-9]{4,6})", message.content)
                    # Only check the message if it has exactly one battletag
                    if len(battletags) == 1:
                        try:
                            # Get the player
                            # noinspection PyProtectedMember
                            player = await pyowapi._get_player(battletags[0])
                        except TimeoutError:
                            # If we time out just return
                            return
                        # If we can't get the player always warn them
                        if not player.success:
                            await message.channel.send(
                                f"{message.author.mention} I can't lookup your profile so lobby leaders may have problems inviting you!\n"
                                f"Usually this is caused by a typo or incorrect CaPiTaLiZaTiOn of your battletag.")
                            return
                        # If the player has a private profile warn them if it's enabled for the current channel
                        if player.private and channel["public_required"]:
                            await message.channel.send(
                                f"{message.author.mention} It looks like your profile is private. It needs to be public if you want to participate in pugs!\n"
                                f"If your profile is already public disregard this, I can only see changes after a game restart.")
                            return
                        # If the player is below level 25 warn them if it's enabled for the current channel
                        if player.actual_level < 25 and channel["level_25_required"]:
                            await message.channel.send(f"{message.author.mention} Your account is below level 25, official pugs require a **placed** account!")
                            return
