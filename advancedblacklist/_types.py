# Copyright (c) 2021 - Amy (jojo7791)
# Licensed under MIT

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Iterable, Union, Literal

import discord.abc
from redbot.core import commands

__all__ = (
    "_WhiteBlacklist",
    "ChannelType",
    "ConfigType",
    "GreedyUserOrRole",
    "UserOrRole",
    "UsersOrRoles",
)

_WhiteBlacklist = Literal["whitelist", "blacklist"]
ChannelType = Union[
    discord.TextChannel,
    discord.abc.PrivateChannel,
    discord.Thread,
]
ConfigType = Union[
    None,
    str,
    int,
    Dict[str, str],
]
UserOrRole = Union[discord.Member, discord.User, discord.Role, int]
UsersOrRoles = Iterable[UserOrRole]

if TYPE_CHECKING:
    GreedyUserOrRole = UsersOrRoles
else:
    GreedyUserOrRole = commands.Greedy[UserOrRole]
