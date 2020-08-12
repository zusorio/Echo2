import helpers
import logging
import discord
from discord.ext import commands, tasks
from airtable import Airtable
from datetime import datetime, timedelta


class MostActive(commands.Cog):
    """Cog for MostActive"""

    def __init__(self, bot: commands.Bot, config: helpers.Config, log: logging.Logger, airtable_api_key: str):
        self.bot = bot
        self.log = log
        self.config = config
        self.log.info("Loaded Cog MostActive")
        self.pug_participants = Airtable(self.config.most_active["airtable_base"], "PUG Participants",
                                         api_key=airtable_api_key)
        self.pug_list = Airtable(self.config.most_active["airtable_base"], "PUG List", api_key=airtable_api_key)

    @commands.command()
    async def most_active(self, ctx: commands.Context, limit: int = 10):
        now = datetime.now().date()
        week_start = now - timedelta(days=now.weekday())
        week_end = week_start + timedelta(days=6)

        this_week_pugs = self.pug_list.get_all(view="Bot View",
                                               formula=f"AND(IS_BEFORE('{week_start}',{'{Time (in GMT)}'}), IS_AFTER('{week_end}',{'{Time (in GMT)}'}))")
        this_week_pug_ids = [pug["id"] for pug in this_week_pugs]
        participants = self.pug_participants.get_all()
        for participant in participants:
            this_week_participated_pugs = list(set(participant["fields"]["Participated PUGs"]) & set(this_week_pug_ids))
            participant['this_week_participated_pugs'] = len(this_week_participated_pugs)
        sorted_participants = sorted(participants,
                                     key=lambda pug_participant: pug_participant['this_week_participated_pugs'])
        sorted_participants.reverse()
        display_limit = min(limit, len(sorted_participants))
        participants_discord_list = []
        for index, participant in enumerate(sorted_participants[:display_limit]):
            participants_discord_list.append(
                f"**{participant['this_week_participated_pugs']}x** - <@{participant['fields']['User ID']}> "
                f"({participant['fields']['Username']}#{participant['fields']['Tag']})")
        participants_discord_text = "\n".join(participants_discord_list)
        embed = discord.Embed(title="This weeks most active PUG Participants",
                              description=f"Data may not be 100% accurate\n{participants_discord_text}",
                              timestamp=datetime.utcnow(),
                              color=0x358bbb)
        embed.set_footer(text="Powered by Echo",
                         icon_url="https://cdn.discordapp.com/app-icons/581523092363411493/9f85d39eb6321ad12b2d13396c4595f5.png?size=256")
        await ctx.send(embed=embed)
