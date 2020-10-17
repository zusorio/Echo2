import asyncio
import logging
import discord
from discord.ext import commands
import helpers


class JTSLock(commands.Cog):
    """
    Locks and unlocks JTS bnet channel
    """

    def __init__(self, bot: commands.Bot, config: helpers.Config, log: logging.Logger):
        self.bot = bot
        self.config = config
        self.log = log
        self.log.info("Loaded Cog JTSLock")

    @commands.command()
    async def lock(self, ctx: commands.Context):
        if ctx.channel.id == self.config.jts_lock["admin_channel_id"]:
            bnet_channel: discord.TextChannel = self.bot.get_channel(self.config.jts_lock["sr_channel_id"])
            target_guild: discord.Guild = self.bot.get_guild(self.config.jts_lock["guild"])
            new_topic = self.config.jts_lock["lock_text"]
            for role_id in self.config.jts_lock["modify_roles"]:
                role: discord.Role = target_guild.get_role(role_id)
                await bnet_channel.set_permissions(role, read_messages=True, send_messages=False)
            await ctx.send("Locked!")
            await ctx.message.add_reaction("✅")
            await bnet_channel.edit(topic=new_topic)

    @commands.command()
    async def unlock(self, ctx: commands.Context):
        if ctx.channel.id == self.config.jts_lock["admin_channel_id"]:
            bnet_channel: discord.TextChannel = self.bot.get_channel(self.config.jts_lock["sr_channel_id"])
            target_guild: discord.Guild = self.bot.get_guild(self.config.jts_lock["guild"])
            for role_id in self.config.jts_lock["modify_roles"]:
                role: discord.Role = target_guild.get_role(role_id)
                await bnet_channel.set_permissions(role, read_messages=True, send_messages=True)
            await ctx.send("Unlocked!")
            await ctx.message.add_reaction("✅")
