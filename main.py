import discord
from discord.ext import commands
from helpers import Config
import logging

from cogs import clean_old_messages, ping_for_messages, disable_reacts, vet_ping_unofficials, purge_channel, reacts_required, delete_match_regex


def main():
    # Read config
    config = Config()

    # Set up logging
    log = logging.getLogger("discord")
    logging.basicConfig(level=logging.INFO)
    log.setLevel(logging.INFO)

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

    # Start bot
    log.warning("Starting Bot...")
    bot.run(config.token)


main()
