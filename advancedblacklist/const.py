"""Different constants for this cog"""

from typing import Any, Dict

_config_structure: Dict[str, Dict[str, Any]] = {
    "global": {
        "blacklist": {},
        "whitelist": {},
        "schema_v1": 1,
    },
    "guild": {
        "blacklist": {},
        "whitelist": {},
    },
}

__authors__ = ["Jojo#7791"]
__version__ = "2.0.3"
