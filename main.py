import discord
from discord.ext import commands
from helpers import Config, Credentials
import logging

from discord_handler import DiscordHandler
from cogs import clean_old_messages, ping_for_messages, disable_reacts, vet_ping_unofficials, purge_channel, \
    reacts_required, delete_match_regex, initialize, warn_wrong_battletags, auto_question_answer, announce, \
    alert_unofficial_start, analytics, most_active, jts_bnets, jts_lock


def main():
    # Read config
    config = Config()
    credentials = Credentials()

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
    webhook_handler = DiscordHandler(credentials.bot_log_webhook, config.bot_log_name)
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
    bot.add_cog(warn_wrong_battletags.WarnWrongBattletags(bot, config, log))
    bot.add_cog(auto_question_answer.AutoQuestionAnswer(bot, config, log))
    bot.add_cog(announce.Announce(bot, config, log, credentials.airtable_api_key))
    bot.add_cog(alert_unofficial_start.AlertUnofficialStart(bot, config, log))
    bot.add_cog(analytics.Analytics(bot, config, log, credentials.airtable_api_key))
    bot.add_cog(most_active.MostActive(bot, config, log, credentials.airtable_api_key))
    bot.add_cog(jts_bnets.JTSBnets(bot, config, log))
    bot.add_cog(jts_lock.JTSLock(bot, config, log))
    bot.add_cog(initialize.Initialize(bot, config, log))

    # Start bot
    log.warning("Starting Bot...")
    bot.run(credentials.token)


main()
