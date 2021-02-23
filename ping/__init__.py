from redbot.core.bot import Red
from redbot.core.commands import command, is_owner

from typing import Optional

__version__ = "0.1.3"


@command()
<<<<<<< HEAD
async def ping(ctx, response: str, mention: bool = False):
    """Pong"""
    await ctx.reply(response, mention_author=mention)
=======
@is_owner()
async def pingset(ctx, mention: Optional[bool] = False, *, response: str = "Pong."):
    """Set the ping command to use replies"""
    bot = ctx.bot
>>>>>>> 27427dcea9c03cf87c2c54841fdcc6eb40f59f7c


def setup(bot: Red):
    bot.remove_command("ping")
    bot.add_command(ping)
