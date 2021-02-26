from redbot.core.bot import Red

from .cycle_status import CycleStatus


async def setup(bot: Red):
    c = CycleStatus(bot)
    bot.add_cog(c)
    await c.init()
