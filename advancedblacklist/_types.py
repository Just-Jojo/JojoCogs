# Copyright (c) 2021 - Amy (jojo7791)
# Licensed under MIT

from __future__ import annotations

import discord.abc
from redbot.core import commands
from typing import Union, Dict, Iterable, TYPE_CHECKING


__all__ = ["ChannelType", "ConfigType", "GreedyUserOrRole", "UserOrRole", "UsersOrRoles"]

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
UserOrRole = Union[int, discord.Member, discord.Member, discord.Role]
UsersOrRoles = Iterable[UserOrRole]

if TYPE_CHECKING:
    GreedyUserOrRole = UsersOrRoles
else:
    GreedyUserOrRole = commands.Greedy[UserOrRole]
