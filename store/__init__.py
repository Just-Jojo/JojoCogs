from redbot.core.bot import Red

from .store import Store


def setup(bot: Red):
    bot.add_cog(Store(bot))
