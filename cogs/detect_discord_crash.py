import logging
import os
import random
import string
import subprocess

import functools
import asyncio
from concurrent.futures import ThreadPoolExecutor
import discord
import wget
from discord.ext import commands
from ffprobe import FFProbe

import helpers


def analyze_video(url):
    # Choose name for video and download it
    vid_id = ''.join([random.choice(string.ascii_lowercase) for _ in range(10)])
    name = wget.download(url, out=f"temp_vids/{vid_id}")

    # Use FFProbe to detect sizes of frames
    frame_size_detect_message = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'frame=width,height', '-select_streams', 'v', '-of',
         'csv=p=0', name],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

    # If frame sizes changes it is a crash gif
    if len(set(filter(None, frame_size_detect_message.stdout.split("\n")))) > 1:
        # Delete the downloaded video
        os.remove(name)
        return True

    # Create jpg of first and last frame
    subprocess.run(
        ['ffmpeg', '-i', name, '-vframes', '1', '-q:v', '1', f'temp_vids/{vid_id}_first.jpg'],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    subprocess.run(
        ['ffmpeg', '-sseof', '-3', '-i', name, '-update', '1', '-q:v', '1', f'temp_vids/{vid_id}_last.jpg'],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

    # Analyze codec of frames
    first_data = FFProbe(f'temp_vids/{vid_id}_first.jpg')
    first_codec = first_data.streams[0].pixel_format()
    last_data = FFProbe(f'temp_vids/{vid_id}_last.jpg')
    last_codec = last_data.streams[0].pixel_format()

    # If codecs changes it is a crash gif
    if first_codec == "yuvj420p" and last_codec == "yuvj444p":
        # Delete the downloaded video and the frames
        os.remove(name)
        os.remove(f'temp_vids/{vid_id}_first.jpg')
        os.remove(f'temp_vids/{vid_id}_last.jpg')
        return True

    return False


class DetectDiscordCrash(commands.Cog):
    """
    Detect Discord Crashing GIFs
    """

    def __init__(self, bot: commands.Bot, config: helpers.Config, log: logging.Logger):
        self.bot = bot
        self.config = config
        self.log = log
        self.log.info("Loaded Cog DetectDiscordCrash")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        for embed in message.embeds:
            if not embed.video or "gfycat.com" not in embed.video.url:
                continue
            self.log.warning(
                f"Scanning Message with content {message.content} posted by {message.author.id} in {message.channel.id} for crash")
            loop = asyncio.get_event_loop()
            is_crash_gif = await loop.run_in_executor(ThreadPoolExecutor(), functools.partial(analyze_video, url=embed.video.url))
            if is_crash_gif:
                await message.delete()
                channel: discord.TextChannel = await self.bot.fetch_channel(
                    self.config.detect_discord_crash["log_channel_id"])
                embed = discord.Embed(title="Deleted crashing GIF",
                                      description=f"Deleted crashing GIF posted by <@{message.author.id}> ({message.author.id}) in <#{message.channel.id}>\nContent is: `{message.content}`",
                                      colour=0xFF0B03)
                embed.set_footer(text="Cerberus by Echo",
                                 icon_url="https://cdn.discordapp.com/app-icons/581523092363411493/9f85d39eb6321ad12b2d13396c4595f5.png?size=256")
                await channel.send(embed=embed)
                self.log.warning(f"Deleted crashing GIF by {message.author.id} in {message.channel.id}, message was {message.content}")
            else:
                self.log.warning(
                    f"Scan is clean for message with content {message.content} posted by {message.author.id} in {message.channel.id} for crash")

