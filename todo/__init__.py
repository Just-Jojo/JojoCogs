from .todo import ToDo


def setup(bot):
    bot.add_cog(ToDo(bot))
