from .pets import Pets
from .pets_v2 import Pets as PetV2

__red_end_user_data_statement__ = "This cog does not persistently store data or metadata about users."


def setup(bot):
    bot.add_cog(PetV2(bot))
