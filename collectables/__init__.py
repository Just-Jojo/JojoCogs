from .collectables import Collectables


def setup(bot):
    cog = Collectables(bot)
    bot.add_listener(cog.listener)
    bot.add_cog(cog)
