import helpers
import logging
import discord
from discord.ext import commands, tasks
from airtable import Airtable


class Analytics(commands.Cog):
    """Cog for PUG Analytics"""

    def __init__(self, bot: commands.Bot, config: helpers.Config, log: logging.Logger, airtable_api_key: str):
        self.bot = bot
        self.log = log
        self.config = config
        self.log.info("Loaded Cog Analytics")
        self.pug_participants = Airtable(self.config.analytics["airtable_base"], "PUG Participants",
                                         api_key=airtable_api_key)
        self.pug_list = Airtable(self.config.analytics["airtable_base"], "PUG List", api_key=airtable_api_key)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState,
                                    after: discord.VoiceState):
        await self.bot.wait_until_ready()
        if after.channel and after.channel.id in self.config.analytics["pug_voice_channels"]:
            active_pug = self.pug_list.get_all(view="Bot View",
                                               formula="AND(IS_AFTER(NOW(), {Time (in GMT)}), {Was Announced} = TRUE())",
                                               maxRecords=1,
                                               sort=[('Time (in GMT)', 'desc')])
            pug_participant = self.pug_participants.get_all(view="Grid view",
                                                            formula=f"{'{'}User ID{'}'} = '{member.id}'")
            if pug_participant:
                if pug_participant[0]["fields"].get("Participated PUGs"):
                    pug_list = pug_participant[0]["fields"]["Participated PUGs"]
                else:
                    pug_list = []
                if active_pug[0]["id"] not in pug_list:
                    pug_list.append(active_pug[0]["id"])
                self.pug_participants.update(record_id=str(pug_participant[0]["id"]),
                                             fields={"Nickname": member.display_name, "Username": member.name, "Participated PUGs": pug_list})
            else:
                self.pug_participants.insert(
                    {"User ID": str(member.id), "Nickname": member.display_name, "Username": member.name, "Participated PUGs": [active_pug[0]["id"]]})
