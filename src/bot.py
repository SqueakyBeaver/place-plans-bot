from dotenv import load_dotenv
from os import getenv
import asyncpraw
from discord.ext import commands
from datetime import datetime
import discord
import re

load_dotenv()
timestamp_regex = re.compile(r"([Xx][Xx]:[0-9][0-9])")  # For that juicy performance


def resolve_timestamp(timestamp: re.Match):
    """
    Attach links to XX:<XX> formatted timestamps for easy planning
    """
    # Since the timestamp is a match object, we have to get the actual matched string
    hh_mm = timestamp[0].split(":")
    now = discord.utils.utcnow()

    day = now.day
    if int(hh_mm[1]) < now.minute:
        hour = now.hour + 1
        if hour >= 24:
            hour -= 25
            day += 1
    else:
        hour = now.hour

    timestamp_time = datetime(
        year=now.year,
        month=now.month,
        day=day,
        hour=hour,
        minute=int(hh_mm[1]),
        second=0,
    )

    return f"[{timestamp[0]}](https://www.timeanddate.com/worldclock/fixedtime.html?iso={timestamp_time.isoformat()})"


def format_latest_commands(text: str):
    text = text.replace("<@&1115073100174860298>", "")  # Remove role mention

    text = re.sub(timestamp_regex, resolve_timestamp, text)

    text += "\n\nJoin the [Discord Server](https://discord.gg/transplace) for faster updates!"

    return text


class DisBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(
            command_prefix=commands.when_mentioned_or("!"),
            intents=discord.Intents.default(),
            *args,
            **kwargs,
        )

    reddit: asyncpraw.Reddit
    transplace_reddit: asyncpraw.reddit.models.Subreddit

    async def on_ready(self):
        self.reddit = asyncpraw.Reddit(
            client_id=getenv("REDDIT_CLIENT_ID"),
            client_secret=getenv("REDDIT_CLIENT_SECRET"),
            refresh_token=getenv("REDDIT_REFRESH_TOKEN"),
            user_agent=getenv("REDDIT_USER_AGENT"),
        )

        self.reddit.validate_on_submit = True

        print("Bot started and ready O7")

    async def setup_hook(self):
        # Not supposed to do this bc of ratelimits, but don't care bc this is a temp bot
        async for i in self.fetch_guilds():
            await self.tree.sync(guild=i)


bot = DisBot()


@bot.tree.context_menu(name="Update orders")
async def publish_to_subreddit(
    interaction: discord.Interaction, message: discord.Message
):
    await interaction.response.defer(ephemeral=True)
    publish_content = format_latest_commands(message.content)
    bot: DisBot = interaction.client

    post: asyncpraw.reddit.models.Submission = await bot.reddit.submission(
        id=getenv("POST_ID")
    )

    await post.edit(publish_content)

    await interaction.followup.send("Updated r/Place Orders O7")


bot.run(getenv("DISCORD_BOT_TOKEN"))
