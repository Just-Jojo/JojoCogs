from redbot.core.bot import Red
from redbot.core.commands import command, is_owner

from typing import Optional

__version__ = "0.1.3"


@command()
async def ping(ctx, response: str, mention: bool = False):
    """Pong"""
    await ctx.reply(response, mention_author=mention)


def setup(bot: Red):
    bot.remove_command("ping")
    bot.add_command(ping)
