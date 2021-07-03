# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

from abc import ABC, abstractmethod

from redbot.core import commands, Config
from redbot.core.bot import Red
from .utils import Cache
from logging import Logger

"""ABCDEFG"""

__all__ = ["TodoMixin", "MetaClass"]


class TodoMixin(ABC):
    """An abstract base class to keep type hints in order"""

    def __init__(self, *_args):
        self.bot: Red
        self.cache: Cache
        self.config: Config
        self.log: Logger

    # The best thing about this is it that I don't have to reimpliment this every time
    # I create a new subclass, just in the main class which will be a subclass of every other class
    @abstractmethod
    async def page_logic(self, ctx: commands.Context, data: list, **settings):
        ...


class MetaClass(type(commands.Cog), type(ABC)):  # type:ignore
    """Meta class for main class"""

    pass
