import logging

import discord
from airbase import Airtable
from discord.ext import commands

import helpers


class Analytics(commands.Cog):
    """Cog for PUG Analytics"""

    def __init__(self, bot: commands.Bot, config: helpers.Config, log: logging.Logger, airtable_api_key: str):
        self.bot = bot
        self.log = log
        self.config = config
        self.log.info("Loaded Cog Analytics")
        self.airtable_api_key = airtable_api_key

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState,
                                    after: discord.VoiceState):
        await self.bot.wait_until_ready()
        async with Airtable(api_key=self.airtable_api_key) as at:
            base = await at.get_base(self.config.announce["airtable_base"], key="id")
            pug_participants = await base.get_table("PUG Participants", key="name")
            pug_list = await base.get_table("PUG List", key="name")

            if after.channel and after.channel.id in self.config.analytics["pug_voice_channels"]:
                active_pug = await pug_list.get_records(view="Bot View",
                                                        filter_by_formula="AND(IS_AFTER(NOW(), {Time (in GMT)}), {Was Announced} = TRUE())")
                pug_participant = await pug_participants.get_records(view="Grid view",
                                                                     filter_by_formula=f"{'{'}User ID{'}'} = '{member.id}'")
                if pug_participant:
                    if pug_participant[0]["fields"].get("Participated PUGs"):
                        pug_list = pug_participant[0]["fields"]["Participated PUGs"]
                    else:
                        pug_list = []
                    if active_pug[0]["id"] not in pug_list:
                        pug_list.append(active_pug[0]["id"])
                    await pug_participants.update_record(record={
                        "id": str(pug_participant[0]["id"]),
                        "fields": {"Nickname": member.display_name, "Username": member.name,
                                   "Tag": member.discriminator, "Participated PUGs": pug_list},
                    })
                else:
                    await pug_participants.post_record(
                        {"fields": {"User ID": str(member.id), "Nickname": member.display_name, "Username": member.name,
                                    "Tag": member.discriminator, "Participated PUGs": [active_pug[0]["id"]]}})
