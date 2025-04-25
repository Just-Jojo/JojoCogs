# Copyright (c) 2021 - Amy (jojo7791)
# Licensed under MIT

from typing import Dict, Final

from ._types import ConfigType


__all__ = ["__author__", "__version__", "config_structure"]


__author__ = "Amy (jojo7791)"
__version__ = "3.0.0.dev1"
default_format: Final[Dict[str, str]] = {
    "title": "{allow_deny_list}",
    "user_or_role": "\t- {user_or_role}: {reason}",
    "footer": "{bot_name} running AdvancedBlacklist {version_info}",
}
config_structure: Dict[str, Dict[str, ConfigType]] = {
    "global": {
        "blacklist": {},
        "whitelist": {},
        "schema_v1": 1,
        "log_channel": None,
        "format": default_format,
    },
    "guild": {
        "blacklist": {},
        "whitelist": {},
    },
}
