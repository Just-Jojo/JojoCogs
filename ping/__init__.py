from redbot.core.bot import Red
from redbot.core.commands import command

__version__ = "0.1.4"


@command()
async def ping(ctx):
    """Pong"""
    await ctx.reply(content="Pong.", mention_author=False)


def setup(bot: Red):
    bot.remove_command("ping")
    bot.add_command(ping)
