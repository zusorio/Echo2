import logging
import discord
import asyncio
from discord.ext import commands
import helpers


class ReactsRequired(commands.Cog):
    def __init__(self, bot: commands.Bot, config: helpers.Config, log: logging.Logger):
        self.bot = bot
        self.config = config
        self.log = log
        self.log.info("Loaded Cog ReactsRequired")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author != self.bot.user:
            for channel in self.config.reacts_required:
                if message.channel.id == channel["reacts_required_channel"]:
                    try:
                        await self.bot.wait_for('reaction_add', timeout=channel["delete_no_reacts_delay_seconds"])
                    except asyncio.TimeoutError:
                        helpers.log_message_deletes([message], "ReactsRequired", self.log)
                        await message.delete()
                        await message.author.send("Your message was deleted because you did not react to it. The channel you used should only be used to start PUGs by following the guide.\n"
                                                  "If you have any questions feel free to ask in questions-for-staff or DM someone but don't use this channel for chatting!")
