# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

from abc import ABC

from redbot.core import commands
from redbot.core.bot import Red


class ABMixin(ABC):
    def __init__(self, *_args):
        self.bot: Red


class CompositeMetaclass(type(ABC), type(commands.Cog)):  # type:ignore
    ...
