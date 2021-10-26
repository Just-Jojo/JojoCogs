# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

from abc import ABC, abstractmethod, abstractstaticmethod
from logging import Logger

import discord
from redbot.core import Config, commands
from redbot.core.bot import Red

from typing import List, Tuple

from .utils import TodoApi

"""ABCDEFG"""

__all__ = ["TodoMixin", "MetaClass"]


class TodoMixin(ABC):
    """An abstract base class to keep type hints in order"""

    def __init__(self, *_args):
        self.bot: Red
        self.cache: TodoApi
        self.config: Config
        self.log: Logger
        self._no_todo_message: str
        self._no_completed_message: str
        self.__authors__: list
        self.__suggestors__: list
        self.__version__: str

    # The best thing about this is it that I don't have to reimpliment this every time
    # I create a new subclass, just in the main class which will be a subclass of every other class
    @abstractmethod
    async def page_logic(self, ctx: commands.Context, data: list, title: str, **settings) -> None:
        ...

    @abstractmethod
    async def _embed_requested(self, ctx: commands.Context, user: discord.User) -> bool:
        ...

    @staticmethod
    @abstractstaticmethod
    async def _get_todos(todos: List[dict]) -> Tuple[List[str], ...]: # type:ignore
        ...

    @staticmethod
    @abstractstaticmethod
    def _gen_timestamp() -> int:
        ...


class MetaClass(type(commands.Cog), type(ABC)): # type:ignore
    """Meta class for main class"""

    pass
