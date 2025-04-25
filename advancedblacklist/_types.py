# Copyright (c) 2021 - Amy (jojo7791)
# Licensed under MIT

from __future__ import annotations

import discord.abc
from typing import Union, Dict, Iterable


__all__ = ["ChannelType", "ConfigType", "UserOrRole", "UsersOrRoles"]

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
UserOrRole = Union[int, discord.User, discord.Member, discord.Role]
UsersOrRoles = Iterable[UserOrRole]
