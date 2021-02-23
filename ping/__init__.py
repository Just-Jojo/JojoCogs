from redbot.core.bot import Red
from redbot.core.commands import command, is_owner

from typing import Optional

__version__ = "0.1.3"


@command()
async def ping(ctx):
    """Pong"""
    await ctx.reply(content="Ping.", mention_author=False)


def setup(bot: Red):
    bot.remove_command("ping")
    bot.add_command(ping)
