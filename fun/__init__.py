from .fun import Fun


def setup(bot):
    bot.add_extension(Fun(bot))
