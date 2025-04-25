# Copyright (c) 2021 - Amy (jojo7791)
# Licensed under MIT

# So, currently Red does not dispatch on blacklisting
# While I would love to add this, I'm not going to :)
# So have this fun stuff


from typing import Any, Callable, Coroutine, Dict, Final, List
from redbot.core.bot import Red


__all__ = ["startup", "destroy"]
initialized: bool = False
Coro = Callable[..., Coroutine[Any, Any, Any]]

_function_names: Final[List[str]] = [
    "add_to_blacklist",
    "remove_from_blacklist",
    "clear_blacklist",
    "add_to_whitelist",
    "remove_from_whitelist",
    "clear_whitelist",
]
_original_functions: Dict[str, Coro] = {}


def patch_wrapper(bot: Red, method_name: str, func: Coro) -> Coro:
    async def inner(*args, **kwargs):
        await func(*args, **kwargs)
        bot.dispatch(f"on_{method_name}")

    return inner


def startup(bot: Red) -> None:
    global initialized
    if initialized:
        return
    initialized = True

    for name in _function_names:
        original = getattr(bot, name)
        _original_functions[name] = original
        setattr(bot, name, patch_wrapper(bot, name, original))
    del name, original


def destroy(bot: Red) -> None:
    global initialized
    if not initialized:
        return
    initialized = False

    for key, value in _original_functions.items():
        setattr(bot, key, value)
    del key, value
