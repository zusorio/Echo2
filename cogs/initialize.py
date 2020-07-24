import helpers
import logging
import discord
import random
import pprint
from datetime import datetime
import subprocess
from discord.ext import commands, tasks


def get_git_revision_short_hash():
    return subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode()


def format_start_message():
    return f"\nEcho2 @ {get_git_revision_short_hash()}" \
           f"It is {datetime.utcnow().isoformat()} UTC\n" \
           f"Startup complete"


class Initialize(commands.Cog):
    """Cog for doing init stuff like setting rich presence"""

    def __init__(self, bot: commands.Bot, config: helpers.Config, log: logging.Logger):
        self.bot = bot
        self.log = log
        self.config = config
        self.log.info("Loaded Cog Initialize")

    async def set_presence(self):
        presence_games = [
            "PUGs",
            "Overwatch",
            "GitGud",
            "VALORANT",
            "PUGGERS",
            "Unofficial PUGs",
            "Coached PUGs",
            "Ranked",
            "elohell.gg",
            "GOATs",
            "3-3",
            "Brigitte",
            "Scrims",
            "e-Sports",
            "eSports",
            "self-isolation"
        ]
        selected_game = random.choice(presence_games)
        await self.bot.change_presence(activity=discord.Game(selected_game))

    @tasks.loop(minutes=30, reconnect=True)
    async def update_presence_auto(self):
        await self.set_presence()

    @commands.Cog.listener()
    async def on_ready(self):
        # Set rich presence and inform us once the bot is ready
        await self.set_presence()
        self.log.info(pprint.pprint(self.config.config_object))
        self.log.warning(format_start_message())
        self.update_presence_auto.start()
