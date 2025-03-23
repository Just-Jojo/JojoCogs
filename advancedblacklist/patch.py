# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

import logging
from typing import Any, Callable, Coroutine, Set, Dict, Final, TypeVar

from redbot.core.bot import Red
from redbot.core._settings_caches import WhitelistBlacklistManager

T = TypeVar("T")
log = logging.getLogger("red.jojocogs.advancedblacklist.patch")
__all__ = ["init", "destory"]

_monkey_patched_names: Final[Set[str, str]] = {
    "add_to_blacklist",
    "remove_from_blacklist",
    "clear_blacklist",
    "add_to_whitelist",
    "remove_from_whitelist",
    "clear_whitelist",
}
CORO = Callable[..., Coroutine[Any, Any, T]]
_original_funcs: Dict[str, CORO] = {}
initialized: bool = False


def init(bot: Red):
    global initialized
    if initialized:
        return
    initialized = True

    for name in _monkey_patched_names:
        origin_function = getattr(WhitelistBlacklistManager, name)
        _original_funcs[name] = origin_function
        setattr(WhitelistBlacklistManager, name, driver(bot, origin_function, name))


def driver(bot: Red, original: CORO, dispatch: str) -> CORO:
    async def function(self: WhitelistBlacklistManager, *a, **kw) -> None:
        await original(self, *a, **kw)
        bot.dispatch(dispatch, *a, **kw)

    return function


def destroy():
    if not initialized:
        return
    # Don't need to set `initialized` here as this will only be called on cog unload
    for key, value in _original_funcs.items():
        setattr(WhitelistBlacklistManager, key, value)
