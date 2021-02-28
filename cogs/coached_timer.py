import asyncio
import logging

import discord
import humanfriendly
from discord.ext import commands

import helpers


def format_remaining(seconds):
    return f"{humanfriendly.format_timespan(seconds)} remaining"


class CoachedTimer(commands.Cog):
    """
    5 Minute timer for coached PUGs
    """

    def __init__(self, bot: commands.Bot, config: helpers.Config, log: logging.Logger):
        self.bot = bot
        self.config = config
        self.log = log
        self.log.info("Loaded Cog CoachedTimer")

    @commands.command()
    async def ptimer(self, ctx: commands.Context, *, timespan: str = "5 minutes"):
        timespan = humanfriendly.parse_timespan(timespan)
        embed = discord.Embed(title="PUG Timer", description=format_remaining(timespan),
                              colour=discord.Colour(0x358bbb))
        embed.set_footer(text="Timer by Echo",
                         icon_url="https://cdn.discordapp.com/app-icons/581523092363411493/9f85d39eb6321ad12b2d13396c4595f5.png?size=256")
        msg: discord.Message = await ctx.send(embed=embed)
        while True:
            await asyncio.sleep(10)
            timespan -= 10
            if timespan > 0:
                embed = discord.Embed(title="PUG Timer", description=format_remaining(timespan),
                                      colour=discord.Colour(0x358bbb))
                embed.set_footer(text="Timer by Echo",
                                 icon_url="https://cdn.discordapp.com/app-icons/581523092363411493/9f85d39eb6321ad12b2d13396c4595f5.png?size=256")
                await msg.edit(embed=embed)
            else:
                await msg.delete()
                await ctx.send(f"{ctx.author.mention} Timer is up!")
                break
