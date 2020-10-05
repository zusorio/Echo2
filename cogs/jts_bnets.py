import logging
import discord
from discord.ext import commands
from helpers import get_possible_correct_tag
import helpers
import pyowapi
import re


class JTSBnets(commands.Cog):
    """
    Enforce SR limits for JTS and correct wrong battletags
    Warns users when their battletags are incorrect
    """

    def __init__(self, bot: commands.Bot, config: helpers.Config, log: logging.Logger):
        self.bot = bot
        self.config = config
        self.log = log
        self.sr_enforce = self.config.jts_bnets["sr_enforce"]
        self.log.info("Loaded Cog JTSBnets")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author != self.bot.user:
            # Check if the message is the JTS bnet channel
            if message.channel.id == self.config.jts_bnets["sr_channel_id"]:
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
                                f"{message.author.mention} That tag seems wrong! **Did you mean**: {correct_tag}\n(No need to post it again though)")
                            return
                        else:
                            await message.channel.send(
                                f"{message.author.mention} That tag seems wrong! **Check if there's a typo!**")
                            return
                    # If the player has a private profile warn them if it's enabled for the current channel
                    if player.private:
                        await message.channel.send(
                            f"{message.author.mention} Please remember to public your profile!\nIf you've already made it public ignore this\n(No need repost your tag)")
                        return
                    # If the player is below level 25 warn them if it's enabled for the current channel
                    if player.actual_level < 25:
                        await message.channel.send(
                            f"{message.author.mention} You cannot participate unless your account is placed!")
                        await message.add_reaction("❗")
                        return
                    # Player above JTS limit
                    player_srs = [player.competitive_tank, player.competitive_damage, player.competitive_support]
                    player_srs = [player_sr for player_sr in player_srs if player_sr is not False]
                    # Must be below sr_limit_low on some roles
                    two_accounts_above_low_limit = sum(
                        [player_sr > self.config.jts_bnets["sr_limit_low"] for player_sr in player_srs]
                    ) >= 2
                    all_accounts_below_high_minimum = all(
                        [player_sr < self.config.jts_bnets["sr_min_high"] for player_sr in player_srs]
                    )
                    all_accounts_above_high_limit = all(
                        [player_sr > self.config.jts_bnets["sr_limit_high"] for player_sr in player_srs]
                    )
                    if two_accounts_above_low_limit and self.sr_enforce == 1:
                        await message.channel.send(
                            f"{message.author.mention} You cannot participate in these PUGs, your SR is too high")
                        await message.add_reaction("❌")
                    elif all_accounts_below_high_minimum and self.sr_enforce == 2:
                        await message.channel.send(
                            f"{message.author.mention} You cannot participate in these PUGs, your SR is too low 😢")
                        await message.add_reaction("❌")
                    elif all_accounts_above_high_limit and self.sr_enforce == 2:
                        await message.channel.send(
                            f"{message.author.mention} You cannot participate in these PUGs, your SR is too high")
                        await message.add_reaction("❌")

    @commands.command()
    async def enable_sr_low(self, ctx: commands.Context):
        if ctx.channel.id == self.config.jts_bnets["admin_channel_id"]:
            self.sr_enforce = 1
            await ctx.message.add_reaction("✅")
            await ctx.send("Enabled SR enforcement in low mode")

    @commands.command()
    async def enable_sr_high(self, ctx: commands.Context):
        if ctx.channel.id == self.config.jts_bnets["admin_channel_id"]:
            self.sr_enforce = 2
            await ctx.message.add_reaction("✅")
            await ctx.send("Enabled SR enforcement in high mode")

    @commands.command()
    async def disable_sr_enforce(self, ctx: commands.Context):
        if ctx.channel.id == self.config.jts_bnets["admin_channel_id"]:
            self.sr_enforce = 0
            await ctx.message.add_reaction("✅")
            await ctx.send("Disabled SR enforcement")
