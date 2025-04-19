# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

from __future__ import annotations

from abc import ABC, ABCMeta, abstractmethod

from logging import Logger
from typing import List, Tuple

import discord
from discord.ext.commands.cog import CogMeta
from redbot.core import Config, commands
from redbot.core.bot import Red

from .utils import TodoApi

"""ABCDEFG"""

__all__ = ["TodoMixin", "MetaClass"]


class TodoMixin(ABC):
    """An abstract base class to keep type hints in order"""

    def __init__(self, bot: Red):
        self.bot: Red
        self.cache: TodoApi
        self.config: Config
        self.log: Logger
        self._no_todo_message: str
        self._no_completed_message: str

    @abstractmethod
    async def page_logic(self, ctx: commands.Context, data: list, title: str, **settings) -> None:
        ...

    @abstractmethod
    async def _embed_requested(self, ctx: commands.Context, user: discord.User) -> bool:
        ...

    @staticmethod
    @abstractmethod
    async def _get_todos(
        todos: List[dict], *, timestamp: bool = False, md: bool = False
    ) -> Tuple[List[str], ...]:  # type:ignore
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def _gen_timestamp() -> int:
        raise NotImplementedError

    @abstractmethod
    async def _embed_colour(self, ctx: commands.Context) -> discord.Colour:
        raise NotImplementedError


class MetaClass(CogMeta, ABCMeta):  # type:ignore
    """Meta class for main class"""

    pass
