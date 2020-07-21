import helpers
import logging
import discord
import humanfriendly
from discord.ext import commands, tasks
from airtable import Airtable

from datetime import datetime, timedelta


class Announce(commands.Cog):
    """Cog for reminding when PUGs are and doing the announcements"""

    def __init__(self, bot: commands.Bot, config: helpers.Config, log: logging.Logger, airtable_api_key: str):
        self.bot = bot
        self.log = log
        self.config = config
        self.log.info("Loaded Cog Announce")
        self.pug_list = Airtable(self.config.announce["airtable_base"], "PUG List", api_key=airtable_api_key)
        self.announce_templates = Airtable(self.config.announce["airtable_base"], "Announce Templates", api_key=airtable_api_key)
        self.check_for_announcements.start()

    @tasks.loop(seconds=2)
    async def check_for_announcements(self):
        await self.bot.wait_until_ready()
        pugs = self.pug_list.get_all(view="Bot View")
        templates = self.announce_templates.get_all(view="Grid view")

        for pug in pugs:
            fields = pug["fields"]
            pug_template = [template for template in templates if template["id"] == fields["Announce Template"][0]][0]
            pug_template_name = pug_template['fields']['Name']
            pug_template_content = pug_template['fields']['Template (Discord Markdown)']

            # The timing breakpoints after which to send out certain announcements
            now = datetime.utcnow()
            date_format = "%Y-%m-%dT%H:%M:%S.%fZ"
            pug_time = datetime.strptime(fields["Time (in GMT)"], date_format)
            pug_reminder_time = pug_time - timedelta(seconds=fields["Remind x before"])
            time_warn_before_announce = self.config.announce["warn_announce_before_minutes"]
            pug_announce_reminder_time = pug_time - timedelta(minutes=time_warn_before_announce)

            # Various strings that we use inside the announcement messages
            pug_reminder_delay_human = humanfriendly.format_timespan(fields['Remind x before'])
            pug_name = f"{fields['Type']} {' Streamed ' if fields.get('Is Streamed') else ''}PUGs"
            pug_type = self.config.announce["types"][fields["Type"]]

            # Airtable fields that are false do not exist (instead of being false) so we have to do this Sadge
            want_remind = fields.get("Auto Remind") is True
            was_reminded = fields.get("Was Reminded") is True
            want_announce = fields.get("Auto Announce") is True
            was_announce_reminded = fields.get("Was Announce Reminded") is True
            was_announced = fields.get("Was Announced") is True

            # Reminder
            if now > pug_reminder_time and want_remind and not was_reminded:
                self.log.warning(f"Reminding Staff of {pug_name} in {pug_reminder_delay_human}")

                reminder_channel = self.bot.get_channel(pug_type["reminder_channel"])
                embed = discord.Embed(
                    title="Availability Check for PUGs",
                    description=f"**{pug_name}** are in {pug_reminder_delay_human}, ping will use {pug_template_name} Template.\nWho is available for these?",
                    colour=discord.Colour(0x358bbb))
                await reminder_channel.send(f"<@&{pug_type['reminder_role']}>")
                await reminder_channel.send(embed=embed)

                # Remind the coaches if it's coached PUGs
                if "Coached" in fields['Type']:
                    self.log.warning(f"Reminding Coaches of {pug_name} in {pug_reminder_delay_human}")
                    for coach_channel in self.config.announce["coach_channels"]:
                        channel = self.bot.get_channel(coach_channel["channel"])
                        embed = discord.Embed(
                            title="Availability Check for Coached PUGs",
                            description=f"**{pug_name}** are in {pug_reminder_delay_human}.\nIf you are available to coach please let us know!",
                            colour=discord.Colour(0x358bbb))
                        await channel.send(f"<@&{coach_channel['role']}>")
                        await channel.send(embed=embed)

                # Update the table that we've done the reminder
                self.pug_list.update(pug["id"], {"Was Reminded": True})

            # Announce reminder
            if now > pug_announce_reminder_time and want_announce and not was_announce_reminded:
                self.log.warning(f"Reminding Staff of upcoming announcement in {pug_name}")

                reminder_channel = self.bot.get_channel(pug_type["reminder_channel"])
                embed = discord.Embed(
                    title=f"Pinging for PUGs in {time_warn_before_announce} minutes",
                    description=f"**{pug_name}** are in {time_warn_before_announce} minutes, ping will use {pug_template_name} Template.\n```{pug_template_content}```",
                    colour=discord.Colour(0x358bbb))
                await reminder_channel.send(f"<@&{pug_type['reminder_role']}>")
                await reminder_channel.send(embed=embed)

                # Update the table that we've done the reminder
                self.pug_list.update(pug["id"], {"Was Announce Reminded": True})

            # Announce
            if now > pug_time and want_announce and not was_announced:
                self.log.warning(f"Announcing {pug_name}")

                announce_channel = self.bot.get_channel(pug_type["announce_channel"])

                await announce_channel.send(pug_template_content)

                # Update the table that we've done the reminder
                self.pug_list.update(pug["id"], {"Was Announced": True})
