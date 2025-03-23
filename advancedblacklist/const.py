"""Different constants for this cog"""

from typing import Any, Dict


__all__ = ["_config_structure", "__authors__", "__version__"]

_config_structure: Dict[str, Dict[str, Any]] = {
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

__authors__ = ["Jojo#7791"]
__version__ = "2.1.3"
