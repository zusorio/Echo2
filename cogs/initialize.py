import helpers
import logging
import discord
from discord.ext import commands
import pprint


def get_safe_config(config: helpers.Config):
    scrubbed_config = config.config_object
    scrubbed_config["token"] = "REDACTED"
    scrubbed_config["bot_log_webhook"] = "REDACTED"
    # Split config into 2000 character blocks because of discords message limit.
    config_string_lines = pprint.pformat(scrubbed_config).splitlines()
    output_messages = []
    current_message = ""
    for line in config_string_lines:
        if len(current_message) + len(line) < 1500:
            current_message += line + "\n"
        else:
            output_messages.append(current_message)
            current_message = ""
    return output_messages


class Initialize(commands.Cog):
    """Cog for doing init stuff like setting rich presence"""

    def __init__(self, bot: commands.Bot, config: helpers.Config, log: logging.Logger):
        self.bot = bot
        self.log = log
        self.config = config
        self.log.info("Loaded Cog Initialize")

    @commands.Cog.listener()
    async def on_ready(self):
        # Set rich presence and inform us once the bot is ready
        activity = discord.Activity(activity=discord.Game("PUGs"))
        await self.bot.change_presence(activity=activity)
        self.log.warning(f"\nConfig:")
        for part in get_safe_config(self.config):
            self.log.warning("\n" + part)
        self.log.warning("Bot is ready, set rich presence")
