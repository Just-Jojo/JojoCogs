# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

import logging
from typing import Any, Callable, Coroutine, Dict, Final, Set, TypeVar

from redbot.core._settings_caches import WhitelistBlacklistManager
from redbot.core.bot import Red

T = TypeVar("T")
log = logging.getLogger("red.jojocogs.advancedblacklist.patch")

__all__ = ["init", "destroy"]

_monkey_patched_names: Final[Set[str]] = {
    "add_to_blacklist",
    "remove_from_blacklist",
    "clear_blacklist",
    "add_to_whitelist",
    "remove_from_whitelist",
    "clear_whitelist",
}

CORO = Callable[..., Coroutine[Any, Any, T]]
_original_funcs: Dict[str, CORO] = {}

# Really don't like using global variables but we ball :3
initialized: bool = False


def init(bot: Red) -> None:
    global initialized
    if initialized:
        return
    initialized = True

    for name in _monkey_patched_names:
        origin_function = getattr(WhitelistBlacklistManager, name)
        _original_funcs[name] = origin_function
        setattr(WhitelistBlacklistManager, name, driver(bot, origin_function, name))
    del name, origin_function


def driver(bot: Red, original: CORO, dispatch: str) -> CORO:
    async def function(self: WhitelistBlacklistManager, *a, **kw) -> None:
        await original(self, *a, **kw)

        # bot.dispatch isn't technically documented
        # however it's used all over red. I will still be careful if anything breaks it
        bot.dispatch(dispatch, *a, **kw)

    return function


def destroy() -> None:
    global initialized
    if not initialized:
        return
    initialized = False

    for key, value in _original_funcs.items():
        setattr(WhitelistBlacklistManager, key, value)
