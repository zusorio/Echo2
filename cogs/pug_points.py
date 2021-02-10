import logging
from datetime import datetime, timedelta
from typing import Optional

import asyncio
import discord
import discord.utils
from airtable import Airtable
from discord.ext import commands, tasks

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
        self.initialize.start()

    @tasks.loop(seconds=1, count=1)
    async def initialize(self):
        # wait until bot is fully ready before starting task, otherwise it breaks
        await self.bot.wait_until_ready()
        # wait for the bot to process the channels and members
        await asyncio.sleep(10)
        self.update_all_roles.start()
        self.log.info("PugPoints is fully ready")

    def calculate_user_points(self, transactions):
        count = 0
        for point_transaction in transactions:
            point_expiry_date = datetime.strptime(point_transaction["fields"]["Lasts Until"], "%Y-%m-%dT%H:%M:%S.%fZ")
            if point_expiry_date - datetime.utcnow() > timedelta(seconds=0):
                count += point_transaction["fields"]["Point Count"]
        return count

    def look_up_user_points(self, user_id: int) -> int:
        point_transactions = self.pug_point_transactions.get_all(view="Grid view",
                                                                 formula=f"{'{'}Captain{'}'} = '{user_id}'")
        return self.calculate_user_points(point_transactions)

    async def award_roles(self, member: discord.Member, point_count: int):
        add_roles = []
        remove_roles = []
        messages = []
        member_roles = [role.id for role in member.roles]
        for reward in self.config.pug_points["rewards"]:
            if point_count >= reward["required_points"] and not reward["role_id"] in member_roles:
                add_roles.append(discord.utils.get(member.guild.roles, id=reward["role_id"]))
                messages.append(f"You have gained the role **{reward['name']}** for being an active Captain!")
            if point_count < reward["required_points"] and reward["role_id"] in member_roles:
                remove_roles.append(discord.utils.get(member.guild.roles, id=reward["role_id"]))
                messages.append(f"Your role **{reward['name']}** has decayed. PUG Points expire after one month.")
        if add_roles:
            await member.add_roles(*add_roles)
        if remove_roles:
            await member.remove_roles(*remove_roles)
        return messages

    @tasks.loop(seconds=60)
    async def update_all_roles(self):
        notification_channel = self.bot.get_channel(self.config.pug_points["notification_channel_id"])
        role_guild = self.bot.get_guild(self.config.pug_points["target_guild"])

        pug_captains = self.pug_captains.get_all(view="Grid view")
        point_transactions = self.pug_point_transactions.get_all(view="Grid view")
        for captain in pug_captains:
            point_count = self.calculate_user_points([point_transaction for point_transaction in point_transactions if
                                                      point_transaction["fields"]["Captain"] == [captain["id"]]])
            captain_member = role_guild.get_member(int(captain["fields"]["User ID"]))
            if not captain_member:
                self.log.warning(f"Captain ID {captain['fields']['User ID']} is malformed")
                continue
            role_messages = await self.award_roles(captain_member, point_count)
            for message in role_messages:
                await notification_channel.send(f"{captain_member.mention} {message}")

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
            {"Transaction Time": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
             "Lasts Until": (datetime.utcnow() + timedelta(weeks=4)).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
             "Point Count": point_count,
             "Captain": [captain_record_id]})

        new_point_count = self.look_up_user_points(member.id)
        await ctx.send(f"{member.display_name} now has {new_point_count} PUG Points")

        role_messages = await self.award_roles(member, new_point_count)
        for message in role_messages:
            await ctx.send(f"{member.mention} {message}")

    @commands.command()
    async def balance(self, ctx: commands.Context, member: Optional[discord.Member] = None):
        await ctx.trigger_typing()
        if member:
            point_count = self.look_up_user_points(member.id)
            await ctx.send(f"{member.display_name} has {point_count} PUG Points")
        else:
            point_count = self.look_up_user_points(ctx.author.id)
            await ctx.send(f"You have {point_count} PUG Points")

    @commands.command()
    async def leaderboard(self, ctx: commands.Context):
        await ctx.trigger_typing()
        role_guild = self.bot.get_guild(self.config.pug_points["target_guild"])
        pug_captains = self.pug_captains.get_all(view="Grid view")
        point_transactions = self.pug_point_transactions.get_all(view="Grid view")
        players = []
        for captain in pug_captains:
            point_count = self.calculate_user_points([point_transaction for point_transaction in point_transactions if
                                                      point_transaction["fields"]["Captain"] == [captain["id"]]])
            captain_member = role_guild.get_member(int(captain["fields"]["User ID"]))
            if point_count > 0:
                players.append({"points": point_count, "mention": captain_member.mention})
        sorted_players = sorted(players, key=lambda k: k["points"])
        sorted_players.reverse()
        sorted_players = sorted_players[:10]
        sorted_players_text = ""
        for count, player in enumerate(sorted_players):
            sorted_players_text += f"{count + 1}. {player['mention']}: {player['points']} PUG Points\n"
        embed = discord.Embed(title="PUG Point leaderboard", description=sorted_players_text)
        await ctx.send(embed=embed)

    @give_points.error
    async def give_points_error(self, ctx: commands.Context, error):
        self.log.warning(f"Got {error}")
        await ctx.send(
            "Got an error while trying to run that command! Make sure to do `%gp @SomeUser#1234` or `%gp @SomeUser#1234 AMOUNT_HERE`")

    @balance.error
    async def balance_error(self, ctx: commands.Context, error):
        self.log.warning(f"Got {error}")
        await ctx.send(
            "Got an error while trying to run that command! Make sure to do `%balance` or `%balance SomeUser#1234`")

    @leaderboard.error
    async def leaderboard_error(self, ctx: commands.Context, error):
        self.log.warning(f"Got {error}")
        await ctx.send("Got an error while trying to run that command!")
