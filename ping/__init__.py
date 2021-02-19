from redbot.core.bot import Red
from redbot.core.commands import command

__version__ = "0.1.0"


@command()
async def pingset(ctx):
    bot = ctx.bot

    @command()
    async def ping(ctx):
        await ctx.reply("Pong.", mention_author=False)

    bot.remove_command("ping")
    bot.add_command(ping)


def setup(bot: Red):
    bot.add_command(pingset)
