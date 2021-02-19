from redbot.core.bot import Red
from redbot.core.commands import command

__version__ = "0.1.1"


@command()
async def pingset(ctx):
    """Set the ping command to use replies"""
    bot = ctx.bot

    @command()
    async def ping(ctx):
        """Pong"""
        await ctx.reply("Pong.", mention_author=False)

    bot.remove_command("ping")
    bot.add_command(ping)
    await ctx.tick()


def setup(bot: Red):
    bot.add_command(pingset)
