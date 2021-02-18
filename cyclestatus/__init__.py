from .cycle_status import CycleStatus
from redbot.core.bot import Red


async def setup(bot: Red):
    c = CycleStatus(bot)
    bot.add_cog(c)
    await c.init()
