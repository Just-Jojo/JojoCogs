from .jojostore import JojoStore


def setup(bot):
    bot.add_cog(JojoStore(bot))
