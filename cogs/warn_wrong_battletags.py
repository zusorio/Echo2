import logging
import discord
from discord.ext import commands
import helpers
import pyowapi
import re
import aiohttp


async def get_possible_correct_tag(wrong_battletag: str):
    async with aiohttp.ClientSession() as session:
        # If they messed up their capitalization this will return the correct capitalization
        # Replace # with %23 as hashtag is not auto encoded for some reason
        async with session.get(f"https://playoverwatch.com/en-us/search/account-by-name/{wrong_battletag.replace('#', '%23')}") as r:
            if r.status == 200:
                profiles = await r.json()
                # Filter the data to only include PC battletags
                profiles = [profile for profile in profiles if profile["platform"] == "pc"]
                # If we have one match that must be it
                if len(profiles) == 1:
                    return profiles[0]["name"]
        # If they messed up their numbers as well see if their bnet name is unique
        async with session.get(f"https://playoverwatch.com/en-us/search/account-by-name/{wrong_battletag.split('#')[0]}") as r:
            if r.status == 200:
                profiles = await r.json()
                # Filter the data to only include PC battletags
                profiles = [profile for profile in profiles if profile["platform"] == "pc"]
                # If we have one match that must be it
                if len(profiles) == 1:
                    return profiles[0]["name"]
        return False


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
                    battletags = re.findall("(?:\\S*)#(?:[0-9]{4,8})", message.content)
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
                            correct_tag = await get_possible_correct_tag(player.bnet)
                            if correct_tag:
                                await message.channel.send(
                                    f"{message.author.mention} That tag seems wrong! **Did you mean**: {correct_tag}")
                                return
                            else:
                                await message.channel.send(
                                    f"{message.author.mention} That tag seems wrong! **Check if there's a typo!**")
                                return
                        # If the player has a private profile warn them if it's enabled for the current channel
                        if player.private and channel["public_required"]:
                            await message.channel.send(
                                f"{message.author.mention} Just a reminder, your profile **needs to be public** when you play in PUGs!\n"
                                f"If it's **already public ignore this**, I'll see it next time once you've restarted your game!")
                            return
                        # If the player is below level 25 warn them if it's enabled for the current channel
                        if player.actual_level < 25 and channel["level_25_required"]:
                            await message.channel.send(f"{message.author.mention} Your account is below level 25, official pugs require a **placed** account!")
                            return
