from .store import Store
from redbot.core.bot import Red


async def setup(bot: Red):
    c = Store(bot)
    await c.init()
    bot.add_cog(c)
