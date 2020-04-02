import logging
import discord
from discord.ext import commands
import helpers


async def get_unique_message_react_users(message: discord.Message) -> list:
    unique_users = []
    # Iterate over all reaction types (So every emoji) on a message
    for reaction_type in message.reactions:
        # Iterate over every reaction from that type
        async for user in reaction_type.users():
            # If the user isn't already in our list add them
            if user not in unique_users:
                unique_users.append(user)
    return unique_users


async def send_ping(message: discord.Message, users_to_mention: list):
    """
    Create an embed with info and post it in the channel of the original message
    :param message: The original message
    :param users_to_mention: List of users to mention
    :return: Nothing
    """
    # Create an embed
    embed = discord.Embed(title=f"{message.author.display_name} said:", description=f"{message.content}", colour=discord.Colour(0x358bbb))
    # Create a string of all the users separated by \n
    users_string = "\n".join(user.mention for user in users_to_mention)
    # Post the message
    await message.channel.send(embed=embed)
    await message.channel.send(users_string)


class PingForMessages(commands.Cog):
    def __init__(self, bot: commands.Bot, config: helpers.Config, log: logging.Logger):
        self.bot = bot
        self.config = config
        self.log = log
        self.log.info("Loaded Cog PingForMessages")

    async def message_was_pinged_earlier(self, message_to_check: discord.Message):
        message: discord.Message
        # Get all the messages in the channel
        async for message in message_to_check.channel.history():
            # If the message has any embeds and the bot made the message
            if message.embeds and message.author == self.bot.user:
                # If the embed for the message contains the message return True
                if message_to_check.content == message.embeds[0].description:
                    return True
        return False

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        # Get the config for the channel the react was in
        channel_configs = [x for x in self.config.ping_for_messages if x["channel_id"] == payload.channel_id]
        # Check if the channel exists
        if channel_configs:
            # Get the message that was reacted to as an object
            reacted_channel = self.bot.get_channel(payload.channel_id)
            reacted_message = await reacted_channel.fetch_message(payload.message_id)
            # Get all users that reacted to the message, without duplicates
            unique_react_users = await get_unique_message_react_users(reacted_message)
            # Make sure the react threshold is met and the message isn't supposed to be ignored
            if len(unique_react_users) >= channel_configs[0]["ping_required_reacts"] and payload.message_id not in channel_configs[0]["ping_ignore_messages"]:
                # Make sure the message has not been pinged for and the bot isn't author
                was_pinged_earlier = await self.message_was_pinged_earlier(reacted_message)
                if not was_pinged_earlier and reacted_message.author != self.bot.user:
                    # Ping for the message
                    self.log.warning(f"Reached reacts, pinging for message {reacted_message.content} from {reacted_message.author.display_name}")
                    await send_ping(reacted_message, unique_react_users)
