# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

from abc import ABC
import discord

from redbot.core import commands
from redbot.core.bot import Red

from typing import Optional, Union


class ABMixin(ABC):
    def __init__(self, *_args):
        self.bot: Red

    def _get_user(
        self, ctx: commands.Context, member_id: str
    ) -> Optional[Union[discord.Member, discord.User]]:
        ...


class CompositeMetaclass(type(ABC), type(commands.Cog)):  # type:ignore
    ...
