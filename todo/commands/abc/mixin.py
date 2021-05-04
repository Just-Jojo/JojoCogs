# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

import logging
from abc import ABC, abstractmethod
from typing import Union

import discord
from redbot.core import Config, commands
from redbot.core.bot import Red


class ToDoMixin(ABC):
    """Mixin allowing for easier type hints"""

    @commands.group()
    @abstractmethod
    async def todo(self, ctx):
        ...

    def __init__(self, *_args):
        self.config: Config
        self.bot: Red
        self.log: logging.Logger
        self._no_completed_message: str
        self._no_todo_message: str
        self._failure_explanation: str

    @abstractmethod
    async def _get_user_config(
        self, user: Union[str, discord.User, discord.Member]
    ) -> dict:
        ...

    @abstractmethod
    async def _get_destination(self, ctx: commands.Context) -> discord.TextChannel:
        ...

    @abstractmethod
    async def update_cache(self) -> None:
        """|coro|

        Updates the settings cache

        credits to phen for sharing this
        https://github.com/phenom4n4n/phen-cogs/blob/1e862ff1f429dfc1c56074f952b75056a79cd246/baron/baron.py#L91
        """
        ...


class CompositeMetaclass(type(commands.Cog), type(ABC)):
    """Metaclass so it doesn't break or something idk"""

    pass
