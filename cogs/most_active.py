import helpers
import logging
import discord
import humanfriendly
from discord.ext import commands, tasks
from airtable import Airtable
from datetime import datetime, timedelta, tzinfo


def get_previous_weeks(seconds: int):
    return datetime.now() - timedelta(seconds=seconds), datetime.now()


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
        self.post_most_active_automatically.start()

    async def get_most_active_players(self, start_time: datetime, end_time: datetime):
        timespan_pug_list = self.pug_list.get_all(view="Bot View",
                                                  formula=f"AND(IS_BEFORE('{start_time}',{'{Time (in GMT)}'}), IS_AFTER('{end_time}',{'{Time (in GMT)}'}))")
        timespan_pug_ids = [pug["id"] for pug in timespan_pug_list]
        participants = self.pug_participants.get_all()
        for participant in participants:
            timespan_participated_pugs = list(set(participant["fields"]["Participated PUGs"]) & set(timespan_pug_ids))
            participant['timespan_participated_pugs'] = len(timespan_participated_pugs)
        sorted_participants = sorted(participants,
                                     key=lambda pug_participant: pug_participant['timespan_participated_pugs'])
        sorted_participants.reverse()
        return sorted_participants

    # @tasks.loop(seconds=1, count=1)
    # async def post_most_active_automatically(self):
    #     await self.bot.wait_until_ready()
    #     while True:
    #         alert_date = datetime.now()
    #         # while alert_date.weekday() != 2:
    #         #     alert_date += timedelta(days=1)
    #         alert_date.replace(hour=22)
    #         self.log.warning(f"Waiting until {alert_date} until next activity reminder")
    #         await discord.utils.sleep_until(alert_date)
    #         self.log.warning("Showing previous week activity")
    #         channel: discord.TextChannel = self.bot.get_channel(self.config.most_active["auto_channel"])
    #         await channel.trigger_typing()
    #
    #         timespan = get_previous_weeks(humanfriendly.parse_timespan("8d"))
    #         friendly_timespan = f"{humanfriendly.format_timespan(timespan[1] - timespan[0])} ago until now"
    #
    #         participants = await self.get_most_active_players(timespan[0], timespan[1])
    #         participants_discord_list = []
    #
    #         for index, participant in enumerate(participants[:20:]):
    #             participants_discord_list.append(
    #                 f"**{participant['timespan_participated_pugs']}x** - <@{participant['fields']['User ID']}> "
    #                 f"({participant['fields']['Username']}#{participant['fields']['Tag']})")
    #         participants_discord_text = "\n".join(participants_discord_list)
    #
    #         embed = discord.Embed(title="This weeks most active PUG Participants",
    #                               description=f"Data may not be 100% accurate\nFrom {friendly_timespan}\n{participants_discord_text}",
    #                               timestamp=datetime.utcnow(),
    #                               color=0x358bbb)
    #         embed.set_footer(text="Powered by Echo",
    #                          icon_url="https://cdn.discordapp.com/app-icons/581523092363411493/9f85d39eb6321ad12b2d13396c4595f5.png?size=256")
    #         await channel.send(embed=embed)

    @commands.command()
    async def most_active(self, ctx: commands.Context, limit: int = 10, *, human_timespan: str = "1 week"):
        await ctx.trigger_typing()

        timespan = get_previous_weeks(humanfriendly.parse_timespan(human_timespan))
        friendly_timespan = f"{humanfriendly.format_timespan(timespan[1] - timespan[0])} ago until now"

        participants = await self.get_most_active_players(timespan[0], timespan[1])
        participants_discord_list = []

        for index, participant in enumerate(participants[:limit:]):
            participants_discord_list.append(
                f"**{participant['timespan_participated_pugs']}x** - <@{participant['fields']['User ID']}> "
                f"({participant['fields']['Username']}#{participant['fields']['Tag']})")
        participants_discord_text = "\n".join(participants_discord_list)

        embed = discord.Embed(title="This weeks most active PUG Participants",
                              description=f"Data may not be 100% accurate\nFrom {friendly_timespan}\n{participants_discord_text}",
                              timestamp=datetime.utcnow(),
                              color=0x358bbb)
        embed.set_footer(text="Powered by Echo",
                         icon_url="https://cdn.discordapp.com/app-icons/581523092363411493/9f85d39eb6321ad12b2d13396c4595f5.png?size=256")
        await ctx.send(embed=embed)

    @most_active.error
    async def most_active_error(self, ctx: commands.Context, error):
        await ctx.send(f"No, I don't think I will.\n\nYou probably did something stupid but just in case yell at Zusor\n```{error}```")
