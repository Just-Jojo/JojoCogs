from .store import Store
from redbot.core.bot import Red


def setup(bot: Red):
    bot.add_cog(Store(bot))
