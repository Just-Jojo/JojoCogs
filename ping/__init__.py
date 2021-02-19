from redbot.core.bot import Red
from redbot.core.commands import command

from typing import Optional

__version__ = "0.1.3"


@command()
async def pingset(ctx, mention: Optional[bool] = False, response: str = "Pong."):
    """Set the ping command to use replies"""
    bot = ctx.bot

    @command()
    async def ping(ctx):
        """Pong"""
        await ctx.reply(response, mention_author=mention)

    bot.remove_command("ping")
    bot.add_command(ping)
    await ctx.tick()


def setup(bot: Red):
    bot.add_command(pingset)
