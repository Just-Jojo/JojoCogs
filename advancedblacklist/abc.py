# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

from abc import ABC, ABCMeta, abstractmethod
from typing import Optional, Union

import discord
from discord.ext.commands.cog import CogMeta
from redbot.core import Config, commands
from redbot.core.bot import Red

from .const import _ChannelType

__all__ = ["ABMixin", "CompositeMetaclass"]


class ABMixin(ABC):
    def __init__(self, bot: Red):
        self.bot: Red
        self.config: Config
        self._log_channel: Optional[_ChannelType]

    @abstractmethod
    def _get_user(
        self, ctx: commands.Context, member_id: str
    ) -> Optional[Union[discord.Member, discord.User]]: ...


class CompositeMetaclass(CogMeta, ABCMeta): ...
