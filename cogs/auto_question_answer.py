import logging
import discord
from discord.ext import commands
import helpers
import re


class AutoQuestionAnswer(commands.Cog):
    """
    Automatically attempts to answer common questions
    """
    def __init__(self, bot: commands.Bot, config: helpers.Config, log: logging.Logger):
        self.bot = bot
        self.config = config
        self.log = log
        self.log.info("Loaded Cog AutoQuestionAnswer")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Message is not from self or another bot and in correct channel
        if message.author != self.bot.user and message.author.bot is not True and message.channel.id in list(self.config.auto_question_answer["question_channels"].values()):
            # Message not from a staff member
            author_role_ids = [role.id for role in message.author.roles]
            if not any([role_id for role_id in author_role_ids if role_id in list(self.config.auto_question_answer["staff_roles"].values())]):
                for question in self.config.auto_question_answer["questions"]:
                    if re.search(question["match"], message.content, re.IGNORECASE):
                        embed = discord.Embed(title=f"This might help: {question['title']}",
                                              description=question["description"],
                                              colour=discord.Colour(0x358bbb))
                        if question.get("image"):
                            embed.set_image(url=question.get("image"))
                        embed.set_footer(text="If this didn't help, press ❌. If it did press ✅")
                        response_message = await message.channel.send(embed=embed)
                        await response_message.add_reaction("❌")
                        await response_message.add_reaction("✅")
                        return

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.Member):
        # Message is from bot and react is not from bot and in correct channel
        if reaction.message.author.id == self.bot.user.id and user.id != self.bot.user.id and reaction.message.channel.id == 701451588593647628:
            # React is for deleting the message
            if reaction.emoji == "❌":
                # Get old embed and change color to red
                embed = reaction.message.embeds[0]
                embed.colour = discord.Colour(0xf1370f)
                await reaction.message.edit(embed=embed)
                # Wait 1.25 seconds because the deletion is kinda jarring otherwise
                await reaction.message.delete(delay=1.25)
            elif reaction.emoji == "✅":
                # Get old embed and change color to green
                embed = reaction.message.embeds[0]
                embed.colour = discord.Colour(0x0fc704)
                await reaction.message.edit(embed=embed)
