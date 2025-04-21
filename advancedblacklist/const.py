"""Different constants for this cog"""

from typing import Dict, Optional, Union

import discord
from discord.abc import PrivateChannel

__all__ = ["_ChannelType", "_config_structure", "__authors__", "__version__"]

__authors__ = ["Jojo#7791"]
__version__ = "2.1.4"
_ChannelType = Union[
    discord.VoiceChannel,
    discord.StageChannel,
    discord.ForumChannel,
    discord.TextChannel,
    discord.CategoryChannel,
    discord.Thread,
    PrivateChannel,
]
_ConfigType = Union[Optional[_ChannelType], int, Dict[str, str]]
_config_structure: Dict[str, Dict[str, _ConfigType]] = {
    "global": {
        "blacklist": {},
        "whitelist": {},
        "schema_v1": 1,
        "log_channel": None,
    },
    "guild": {
        "blacklist": {},
        "whitelist": {},
    },
}
