from .jojo_eco import JojoEconomy

def setup(bot):
    bot.add_cog(JojoEconomy(bot))