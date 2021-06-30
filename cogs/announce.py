import helpers
import logging
import discord
import humanfriendly
from discord.ext import commands, tasks
from airbase import Airtable

from datetime import datetime, timedelta


class Announce(commands.Cog):
    """Cog for reminding when PUGs are and doing the announcements"""

    def __init__(self, bot: commands.Bot, config: helpers.Config, log: logging.Logger, airtable_api_key: str):
        self.bot = bot
        self.log = log
        self.config = config
        self.log.info("Loaded Cog Announce")
        self.airtable_api_key = airtable_api_key
        self.check_for_announcements.start()

    @tasks.loop(seconds=20, reconnect=True)
    async def check_for_announcements(self):
        await self.bot.wait_until_ready()

        async with Airtable(api_key=self.airtable_api_key) as at:
            base = await at.get_base(self.config.announce["airtable_base"], key="id")
            pug_list = await base.get_table("PUG List", key="name")
            announce_templates = await base.get_table("Announce Templates", key="name")
            pugs = await pug_list.get_records(view="Bot View")
            templates = await announce_templates.get_records(view="Grid view")

            for pug in pugs:
                fields = pug["fields"]

                is_valid = True

                # All these fields need to be present, else mark as invalid
                required_fields = ["Time (in GMT)", "Type", "Announce Template"]
                for required_field in required_fields:
                    if not fields.get(required_field):
                        is_valid = False

                # If there is no announcement no action is required and we continue
                if fields.get("Auto Remind") is not True and fields.get("Auto Announce") is not True:
                    continue

                # If the row is invalid ignore it
                if not is_valid:
                    self.log.info(f"Ignoring {fields['PUG ID']} due to missing fields")
                    continue

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
                    await reminder_channel.send(content=f"<@&{pug_type['reminder_role']}>", embed=embed)

                    # Remind the coaches if it's coached PUGs
                    if "Coached" in fields['Type']:
                        self.log.warning(f"Reminding Coaches of {pug_name} in {pug_reminder_delay_human}")
                        for coach_channel in self.config.announce["coach_channels"]:
                            channel = self.bot.get_channel(coach_channel["channel"])
                            embed = discord.Embed(
                                title="Availability Check for Coached PUGs",
                                description=f"**{pug_name}** are in {pug_reminder_delay_human}.\nIf you are available to coach please let us know!",
                                colour=discord.Colour(0x358bbb))
                            await channel.send(content=f"<@&{coach_channel['role']}>", embed=embed)

                    # Update the table that we've done the reminder
                    await pug_list.update_record(record={
                        "id": pug["id"],
                        "fields": {"Was Reminded": True},
                    })

                # Announce reminder
                if now > pug_announce_reminder_time and want_announce and not was_announce_reminded:
                    self.log.warning(f"Reminding Staff of upcoming announcement in {pug_name}")

                    reminder_channel = self.bot.get_channel(pug_type["reminder_channel"])
                    embed = discord.Embed(
                        title=f"Pinging for PUGs in {time_warn_before_announce} minutes",
                        description=f"**{pug_name}** are in {time_warn_before_announce} minutes, ping will use {pug_template_name} Template.\n```{pug_template_content}```",
                        colour=discord.Colour(0x358bbb))
                    await reminder_channel.send(content=f"<@&{pug_type['reminder_role']}>", embed=embed)

                    # Update the table that we've done the reminder
                    await pug_list.update_record(record={
                        "id": pug["id"],
                        "fields": {"Was Announce Reminded": True},
                    })

                # Announce
                if now > pug_time and want_announce and not was_announced:
                    self.log.warning(f"Announcing {pug_name}")

                    announce_channel = self.bot.get_channel(pug_type["announce_channel"])

                    message = await announce_channel.send(pug_template_content)
                    if message.channel.is_news():
                        await message.publish()
                    # Update the table that we've done the reminder
                    await pug_list.update_record(record={
                        "id": pug["id"],
                        "fields": {"Was Announced": True},
                    })
