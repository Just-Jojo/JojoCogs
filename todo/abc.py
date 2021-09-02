# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

from abc import ABC, abstractmethod
from logging import Logger

import discord
from redbot.core import Config, commands
from redbot.core.bot import Red

from .utils import Cache

"""ABCDEFG"""

__all__ = ["TodoMixin", "MetaClass"]


class TodoMixin(ABC):
    """An abstract base class to keep type hints in order"""

    def __init__(self, *_args):
        self.bot: Red
        self.cache: Cache
        self.config: Config
        self.log: Logger
        self._no_todo_message: str
        self._no_completed_message: str

    # The best thing about this is it that I don't have to reimpliment this every time
    # I create a new subclass, just in the main class which will be a subclass of every other class
    @abstractmethod
    async def page_logic(self, ctx: commands.Context, data: list, **settings) -> None:
        ...

    @abstractmethod
    async def _embed_requested(self, ctx: commands.Context, user: discord.User) -> bool:
        ...


class MetaClass(type(commands.Cog), type(ABC)):
    """Meta class for main class"""

    pass
