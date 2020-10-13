from .pets import Pets


def setup(bot):
    bot.add_cog(Pets(bot))
