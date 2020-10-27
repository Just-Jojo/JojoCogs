from .swearcount import SwearCount


def setup(bot):
    cog = SwearCount(bot)
    # bot.add_listener(cog.listener, "on_message")
    bot.add_cog(cog)
