"""Different constants for this cog"""

from typing import Any, Dict

_config_structure: Dict[str, Dict[str, Any]] = {
    "global": {
        "blacklist": {},
        "whitelist": {},
    },
    "guild": {
        "blacklist": {},
        "whitelist": {},
    },
}

__version__ = "2.0.0.dev1"


class _Lazy(list):
    """Jojo is lazy"""

    def tick_self(self):
        return [f"`{x}`" for x in self]


__authors__ = _Lazy(["Jojo#7791"])
