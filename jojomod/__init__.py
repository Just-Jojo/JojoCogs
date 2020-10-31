from .jojomod import JojoMod


def setup(bot):
    cog = JojoMod(bot)
    bot.add_cog(cog)
