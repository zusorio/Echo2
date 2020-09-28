import json
import codecs
import discord
import logging
import aiohttp
from typing import List


class Config:
    def __init__(self):
        try:
            with codecs.open("config.json", "r", encoding='utf-8') as config_file:
                self.config_object = json.load(config_file)
        except FileNotFoundError:
            raise SystemExit("Could not find config")
        self.bot_prefix = self.config_object["bot_prefix"]
        self.bot_log_name = self.config_object["bot_log_name"]
        self.clean_old_messages = self.config_object["clean_old_messages"]
        self.ping_for_messages = self.config_object["ping_for_messages"]
        self.disable_reacts = self.config_object["disable_reacts"]
        self.vet_ping_unofficials = self.config_object["vet_ping_unofficials"]
        self.purge_channel = self.config_object["purge_channel"]
        self.reacts_required = self.config_object["reacts_required"]
        self.delete_match_regex = self.config_object["delete_match_regex"]
        self.warn_wrong_battletags = self.config_object["warn_wrong_battletags"]
        self.auto_question_answer = self.config_object["auto_question_answer"]
        self.announce = self.config_object["announce"]
        self.alert_unofficial_start = self.config_object["alert_unofficial_start"]
        self.analytics = self.config_object["analytics"]
        self.most_active = self.config_object["most_active"]
        self.jts_bnets = self.config_object["jts_bnets"]


class Credentials:
    def __init__(self):
        try:
            with codecs.open("credentials.json", "r", encoding='utf-8') as config_file:
                self.config_object = json.load(config_file)
        except FileNotFoundError:
            raise SystemExit("Could not find config")
        self.token = self.config_object["bot_token"]
        self.bot_log_webhook = self.config_object["webhook"]
        self.airtable_api_key = self.config_object["airtable_api_key"]


def log_message_deletes(messages: List[discord.Message], action_name: str, log: logging.Logger):
    if len(messages) == 1:
        log.warning(f"{action_name} deleted 1 message: {messages[0].content if messages[0].content else 'embed'} by {messages[0].author.display_name}")
    elif len(messages) > 1:
        messages_formatted = '\n  '.join([f"{message.content} by {message.author.display_name}" if message.content else f"embed by {message.author.display_name}" for message in messages])
        log.warning(f"{action_name} deleted {len(messages)} messages:\n"
                    f"  {messages_formatted}")


async def get_possible_correct_tag(wrong_battletag: str):
    async with aiohttp.ClientSession() as session:
        # If they messed up their capitalization this will return the correct capitalization
        # Replace # with %23 as hashtag is not auto encoded for some reason
        async with session.get(
                f"https://playoverwatch.com/en-us/search/account-by-name/{wrong_battletag.replace('#', '%23')}") as r:
            if r.status == 200:
                profiles = await r.json()
                # Filter the data to only include PC battletags
                profiles = [profile for profile in profiles if profile["platform"] == "pc"]
                # If we have one match that must be it
                if len(profiles) == 1:
                    return profiles[0]["name"]
        # If they messed up their numbers as well see if their bnet name is unique
        async with session.get(
                f"https://playoverwatch.com/en-us/search/account-by-name/{wrong_battletag.split('#')[0]}") as r:
            if r.status == 200:
                profiles = await r.json()
                # Filter the data to only include PC battletags
                profiles = [profile for profile in profiles if profile["platform"] == "pc"]
                # If we have one match that must be it
                if len(profiles) == 1:
                    return profiles[0]["name"]
        return False
