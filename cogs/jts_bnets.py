import logging
from typing import List

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
        self.preset = False
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
                                f"{message.author.mention} That tag seems wrong! **Did you mean**: {correct_tag}? Then edit your message")
                            return
                        else:
                            await message.channel.send(
                                f"{message.author.mention} That tag seems wrong! **Check if there's a typo and then edit your message!**")
                            return
                    # If the player has a private profile warn them if it's enabled for the current channel
                    if player.private:
                        await message.channel.send(
                            f"{message.author.mention} Please remember to public your profile!\nIf it's public ignore \n(No need repost your tag)")
                        return
                    # If the player is below level 25 warn them if it's enabled for the current channel
                    if player.actual_level < 25:
                        await message.channel.send(
                            f"{message.author.mention} You cannot participate unless your account is placed!")
                        await message.add_reaction("❗")
                        return
                    preset = [preset for preset in self.config.jts_bnets["presets"] if preset["name"] == self.preset]
                    if len(preset) == 1:
                        # Set preset to first with matching name
                        preset = preset[0]
                        # Aggregate Player SR
                        player_srs = [player.competitive_tank, player.competitive_damage, player.competitive_support]
                        player_srs = [player_sr for player_sr in player_srs if player_sr is not False]
                        for rule in preset["rules"]:
                            # srs_not_matching_rule will be a list containing True for every sr not matching the rule
                            # and false for srs matching the rule
                            # so if the max sr is 2500 and the player sr's are 2200, 2400, 2600
                            # it will be [False, False, True]
                            srs_not_matching_rule: List[bool]
                            if rule["mode"] == "min":
                                srs_not_matching_rule = [player_sr < rule["sr"] for player_sr in player_srs]
                            elif rule["mode"] == "max":
                                srs_not_matching_rule = [player_sr >= rule["sr"] for player_sr in player_srs]
                            else:
                                # Mode is wrong, ignore the rule
                                self.log.warning(f"Ignoring rule {preset['name']} due to invalid mode")
                                continue
                            # count_for_fail indicates when the rule will fail
                            if rule["count_for_fail"] == "all":
                                # If all placed roles are above max/below min
                                rule_triggered = sum(srs_not_matching_rule) == len(srs_not_matching_rule)
                            elif rule["count_for_fail"] == "any":
                                # If any placed roles are above max/below min
                                rule_triggered = any(srs_not_matching_rule)
                            elif rule["count_for_fail"] == "2":
                                # If at least 2 placed roles above max/below min
                                rule_triggered = sum(srs_not_matching_rule) >= 2
                            else:
                                # count_for_fail is wrong, ignore rule
                                self.log.warning(f"Ignoring rule {preset['name']} due to invalid count_for_fail")
                                continue
                            # If the rule got triggered warn the player
                            if rule_triggered and rule["mode"] == "min":
                                await message.channel.send(
                                    f"{message.author.mention} You cannot participate in these PUGs, your SR is too low 😢")
                                await message.add_reaction("❌")
                            elif rule_triggered and rule["mode"] == "max":
                                await message.channel.send(
                                    f"{message.author.mention} You cannot participate in these PUGs, your SR is too high")
                                await message.add_reaction("❌")

    @commands.command()
    async def sr_preset(self, ctx: commands.Context, mode_name: str):
        if ctx.channel.id == self.config.jts_bnets["admin_channel_id"]:
            self.preset = mode_name
            presets = [preset for preset in self.config.jts_bnets["presets"] if preset["name"] == self.preset]
            # If we can't find exactly 1 preset error
            if len(presets) != 1:
                await ctx.send("Hmm, I can't find that preset!")
                return
            # Set preset to the only preset
            preset = presets[0]
            # Confirm change to user
            await ctx.message.add_reaction("✅")
            await ctx.send(f"Set mode to {mode_name}")
            # Edit channel to preset's description
            channel: discord.TextChannel = self.bot.get_channel(self.config.jts_bnets["sr_channel_id"])
            await channel.edit(topic=preset["channel_description"])
