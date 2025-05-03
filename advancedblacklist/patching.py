# Copyright (c) 2021 - Amy (jojo7791)
# Licensed under MIT

# So, currently Red does not dispatch on blacklisting
# While I would love to add this, I'm not going to :)
# So have this fun stuff


import asyncio
import logging
from typing import TYPE_CHECKING, Any, Callable, Coroutine, Dict, Final, List
from functools import wraps

from discord.utils import maybe_coroutine
from redbot.core.bot import Red


__all__ = ["Patch"]

_log = logging.getLogger("redbot.jojocogs.advancedblacklist.patch")
Coro = Callable[..., Coroutine[Any, Any, Any]]
_lock = asyncio.Lock()
_names: Final[List[str]] = [
    "add_to_blacklist",
    "remove_from_blacklist",
    "clear_blacklist",
    "add_to_whitelist",
    "remove_from_whitelist",
    "clear_whitelist",
]


def _with_lock(func: Callable[[Any], Any]) -> Coro:
    @wraps(func)
    async def inner(*args, **kwargs) -> Any:
        async with _lock:
            return await maybe_coroutine(func, *args, **kwargs)

    return inner


class Patch:
    def __init__(self, bot: Red):
        self.bot = bot
        self._funcs: Dict[str, Coro] = {}
        self._initialized = False

    def _patch_wrapper(self, method_name: str, func: Coro) -> Coro:
        @wraps(func)
        async def inner(*args, **kwargs):
            adv_bl = kwargs.pop("adv_bl", False)
            await func(*args, **kwargs)
            self.bot.dispatch(f"on_{method_name}", *args, **kwargs, adv_bl=adv_bl)

        return inner

    @_with_lock
    def startup(self) -> None:
        if self._initialized:
            return
        for name in _names:
            func = getattr(self.bot, name)
            if not func:
                # Shouldn't really happen let's log just in case
                _log.warning(
                    f"Couldn't find {name}, skipping replacement\n"
                    "Please make an issue if this persists (https://github.com/Just-Jojo/JojoCogs)"
                )
                continue

            self._funcs[name] = func
            setattr(self.bot, name, self._patch_wrapper(name, func))
        self._initialized = True

    @_with_lock
    def destroy(self) -> None:
        if not self._initialized:
            return

        # NOTE this shouldn't really need to be here
        # as I should only be calling this when the cog unloads
        # but just in case
        self._initialized = False

        for name, func in self._funcs.items():
            setattr(self.bot, name, func)
