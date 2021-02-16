from discord import version_info

if version_info[:2] >= (1, 6):
    from .todo import ToDo
else:
    from .todo_15 import ToDo


def setup(bot):
    bot.add_cog(ToDo(bot))
