import discord
from discord.ext import commands
from helpers import Config
import logging

from discord_handler import DiscordHandler
from cogs import clean_old_messages, ping_for_messages, disable_reacts, vet_ping_unofficials, purge_channel, reacts_required, delete_match_regex, initialize


def main():
    # Read config
    config = Config()

    # Set up logging
    format = logging.Formatter(
        "{asctime} [{levelname}] [{module}] {message}",
        style="{",
        datefmt="%H:%M:%S"
    )

    # Get the discord logger
    log = logging.getLogger("discord")
    # Set logging level to debug for now
    log.setLevel(logging.INFO)

    # Create a handler that outputs INFO to stdout
    text_handler = logging.StreamHandler()
    text_handler.setLevel(logging.INFO)
    text_handler.setFormatter(format)
    log.addHandler(text_handler)

    # Create a handler that outputs WARNING to the discord webhook
    webhook_handler = DiscordHandler(config.bot_log_webhook, config.bot_log_webhook)
    webhook_handler.setLevel(logging.WARNING)
    webhook_handler.setFormatter(format)
    log.addHandler(webhook_handler)

    # Initialize bot object
    bot = commands.Bot(command_prefix=config.bot_prefix)

    # Load cogs
    bot.add_cog(clean_old_messages.CleanOldMessages(bot, config, log))
    bot.add_cog(ping_for_messages.PingForMessages(bot, config, log))
    bot.add_cog(disable_reacts.DisableReacts(bot, config, log))
    bot.add_cog(vet_ping_unofficials.VetPingUnofficials(bot, config, log))
    bot.add_cog(purge_channel.PurgeChannel(bot, config, log))
    bot.add_cog(reacts_required.ReactsRequired(bot, config, log))
    bot.add_cog(delete_match_regex.DeleteMatchRegEx(bot, config, log))
    bot.add_cog(initialize.Initialize(bot, config, log))

    # Start bot
    log.warning("Starting Bot...")
    bot.run(config.token)


main()
