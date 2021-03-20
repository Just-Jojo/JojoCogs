from redbot.core.bot import Red
from redbot.core.commands import command, Command

__version__ = "0.1.4"

OLD_PING: Command = None


@command(hidden=True)
async def ping(ctx):
    """Pong"""
    await ctx.reply(content="Pong.", mention_author=False)


def setup(bot: Red):
    global OLD_PING
    OLD_PING = bot.remove_command("ping")

    bot.add_command(ping)


def teardown(bot: Red):
    bot.remove_command("ping")
    global OLD_PING
    if OLD_PING:
        bot.add_command(OLD_PING)
