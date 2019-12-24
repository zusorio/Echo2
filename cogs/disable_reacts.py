import logging
import discord
from discord.ext import commands
import helpers


def check_emoji_allowed(emoji, message_exceptions):
    # Used to make sure the emoji is allowed. This is needed as there are unicode and discord emoji
    if isinstance(emoji, str):
        return emoji in message_exceptions
    else:
        return emoji.id in message_exceptions


class DisableReacts(commands.Cog):
    """
    Used to disable reacts on certain messages except for certain exceptions.
    """
    def __init__(self, bot: commands.Bot, config: helpers.Config, log: logging.Logger):
        self.bot = bot
        self.config = config
        self.log = log
        self.log.info("Loaded Cog DisableReacts")
        # self.remove_reacts_initial.start()

    # This would auto remove emoji on disallowed messages, not using due to rate limits
    async def remove_reacts_initial(self):
        await self.bot.wait_until_ready()
        # Go over all messages with disabled reacts
        for message in self.config.disable_reacts:
            message_object: discord.Message
            # Get the actual message
            channel = discord.utils.get(self.bot.get_all_channels(), id=message["channel_id"])
            message_object = await channel.fetch_message(message["message_id"])
            # Delete all reacts that ar enot allowed
            for react in message_object.reactions:
                if not check_emoji_allowed(react.emoji, message["exceptions"]):
                    async for user in react.users():
                        await message_object.remove_reaction(react, user)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        for message in self.config.disable_reacts:
            if message["message_id"] == payload.message_id:
                # If the reacts isn't allowed
                if not check_emoji_allowed(payload.emoji, message["exceptions"]):
                    # Get the react and delete it
                    guild = self.bot.get_guild(payload.guild_id)
                    reacted_message = await guild.get_channel(payload.channel_id).fetch_message(payload.message_id)
                    user = guild.get_member(payload.user_id)
                    await reacted_message.remove_reaction(payload.emoji, user)
                    await user.send("Please don't add spam reactions to this message!")
