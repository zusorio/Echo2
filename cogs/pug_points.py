import logging
from datetime import datetime
from typing import Optional

import discord
from airtable import Airtable
from discord.ext import commands

import helpers


class PugPoints(commands.Cog):
    """Cog for PUG Points"""

    def __init__(self, bot: commands.Bot, config: helpers.Config, log: logging.Logger, airtable_api_key: str):
        self.bot = bot
        self.log = log
        self.config = config
        self.log.info("Loaded Cog PUG Points")
        self.pug_captains = Airtable(self.config.pug_points["airtable_base"], "Captains", api_key=airtable_api_key)
        self.pug_point_transactions = Airtable(self.config.pug_points["airtable_base"], "Point Transactions",
                                               api_key=airtable_api_key)

    def get_user_points(self, user_id: int) -> int:
        point_transactions = self.pug_point_transactions.get_all(view="Grid view",
                                                                 formula=f"{'{'}Captain{'}'} = '{user_id}'")
        count = sum([point_transaction["fields"]["Point Count"] for point_transaction in point_transactions])
        return count

    @commands.command(name="gp")
    async def give_points(self, ctx: commands.Context, member: discord.Member, point_count: int = 1):
        is_allowed = any([role.id for role in ctx.author.roles if role.id in self.config.pug_points["allowed_roles"]])
        if not is_allowed:
            await ctx.send("No, I don't think I will")
            return
        await ctx.trigger_typing()
        pug_captain = self.pug_captains.get_all(view="Grid view", formula=f"{'{'}User ID{'}'} = '{member.id}'")

        # Get captain ID if they exist, create them and get the id if they didn't
        if pug_captain:
            captain_record_id = pug_captain[0]["id"]
        else:
            pug_captain = self.pug_captains.insert(
                {"User ID": str(member.id), "Nickname": member.display_name, "Username": member.name,
                 "Tag": member.discriminator})
            captain_record_id = pug_captain["id"]

        self.pug_point_transactions.insert(
            {"Transaction Time": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"), "Point Count": point_count,
             "Captain": [captain_record_id]})
        point_count = self.get_user_points(member.id)
        await ctx.send(f"{member.display_name} now has {point_count} ScrimBux")

    @commands.command()
    async def balance(self, ctx: commands.Context, member: Optional[discord.Member] = None):
        await ctx.trigger_typing()
        if member:
            point_count = self.get_user_points(member.id)
            await ctx.send(f"{member.display_name} has {point_count} ScrimBux")
        else:
            point_count = self.get_user_points(ctx.author.id)
            await ctx.send(f"You have {point_count} ScrimBux")

    @give_points.error
    async def give_points_error(self, ctx: commands.Context, error):
        self.log.warning(f"Got {error}")
        await ctx.send(
            "Got an error while trying to run that command! Make sure to do `!give_points @SomeUser#1234` or `!give_points @SomeUser#1234 AMOUNT_HERE`")

    @balance.error
    async def balance_error(self, ctx: commands.Context, error):
        self.log.warning(f"Got {error}")
        await ctx.send(
            "Got an error while trying to run that command! Make sure to do `!balance` or `!balance SomeUser#1234`")
