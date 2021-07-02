# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

import logging
import typing
from typing import Union, Any, Optional, Dict
from abc import ABC, abstractmethod

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
        self, user: Union[int, discord.Member, discord.User]
    ) -> Dict[str, typing.Any]:
        ...

    @abstractmethod
    async def _get_destination(
        self, ctx: commands.Context, *, private: bool
    ) -> discord.TextChannel:
        ...

    @abstractmethod
    async def update_cache(self, *, user_id: int = None) -> None:
        """|coro|

        Updates the settings cache

        credits to phen for sharing this
        https://github.com/phenom4n4n/phen-cogs/blob/1e862ff1f429dfc1c56074f952b75056a79cd246/baron/baron.py#L91
        """
        ...

    @abstractmethod
    async def _maybe_autosort(self, ctx: commands.Context) -> None:
        ...

    @abstractmethod
    async def page_logic(
        self,
        ctx: commands.Context,
        data: list,
        title: str,
        *,
        use_md: bool,
        use_embeds: bool,
        private: bool,
        colour: Optional[Union[str, int]],
        timestamp: bool,
    ):
        ...


class CompositeMetaclass(type(commands.Cog), type(ABC)):  # type:ignore[misc]
    """Metaclass so it doesn't break or something idk"""

    pass
