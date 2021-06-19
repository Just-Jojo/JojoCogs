import json
from pathlib import Path

from .update import UpdateUtils

# TODO Code for info.json stuff


def setup(bot):
    bot.add_cog(UpdateUtils(bot))
