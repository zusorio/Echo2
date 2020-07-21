import logging
import discord
import asyncio
from discord.ext import commands
import helpers


class AlertUnofficialStart(commands.Cog):
    """
    Post when someone is trying to start an unofficial PUGs
    """
    def __init__(self, bot: commands.Bot, config: helpers.Config, log: logging.Logger):
        self.bot = bot
        self.config = config
        self.log = log
        self.log.info("Loaded Cog AlertUnofficialStart")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Message is not from self or another bot
        if message.author != self.bot.user and message.author.bot is not True:
            for alert_channel in self.config.alert_unofficial_start["alert_receive_channels"]:
                # If the message is in the correct channel and isn't protected or a lobby info (Lobby UA)
                if message.channel.id == alert_channel["channel"]:
                    try:
                        reacted_messages = await self.bot.wait_for('reaction_add', timeout=60)
                        was_reacted = len(reacted_messages) >= 2
                        if was_reacted:
                            self.log.warning(f"Unofficial PUG starting explainer sent")
                            channel = self.bot.get_channel(self.config.alert_unofficial_start["alert_send_channel"])
                            embed = discord.Embed(title="Someone is trying to start an unofficial PUG!", description=message.content, color=0x358bbb)
                            embed.add_field(name="How to join", value=f"Go to <#{message.channel.id}> and react to the post, then join when you get pinged", inline=False)
                            embed.add_field(name="I can't see the channel", value=f"Go to <#718355765517090848> and give yourself the PUG role", inline=True)
                            embed.add_field(name="The message is gone!", value=f"We periodically delete old messages. Feel free to make a new post though!", inline=True)
                            embed.set_author(name=message.author.display_name, icon_url=message.author.avatar_url)
                            await channel.send(embed=embed)
                    except asyncio.TimeoutError:
                        pass
