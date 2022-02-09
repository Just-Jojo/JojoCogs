# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

# This file contains some code from TrustyJAID's retrigger cog, which is licensed under MIT
# https://github.com/TrustyJAID/trusty-cogs/
# MIT License

# Copyright (c) 2017 TrustyJAID

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import asyncio
import functools
import logging
import multiprocessing as mp
from multiprocessing.pool import Pool
from typing import (Any, AsyncGenerator, Callable, Coroutine, Dict, Iterable,
                    List, Optional, Tuple, TypeVar, Union)

import discord
from redbot.core import Config, commands
from redbot.core.bot import Red

from ..consts import config_structure

try:
    import regex as re
except ImportError:
    import re  # type:ignore

User = Union[int, discord.Member, discord.User]
__all__ = [
    "TodoApi",
]

"""
Hi there. If you're reading this this means that you're reading this.

This bit of code below me is part of my most brilliant pieces of code produced in my insanity whilst rebuilding this cog.
It's design is so odd and frankly strange that I doubt I will be able to replicate it at any point further.

All this is to say that I don't know why I built this cog and I hate myself :D
"""

log = logging.getLogger("red.jojocogs.todo.api")
T = TypeVar("T")
Coro = Callable[..., Coroutine[Any, Any, T]]


async def async_filter(async_pred: Coro, iterable: Iterable[Any]) -> AsyncGenerator[Any, None]:
    for item in iterable:
        if await async_pred(item):
            yield item


class InvalidRegex(commands.UserFeedbackCheckFailure):
    def __init__(self):
        super().__init__(message="That regex is invalid.")


class TodoApi:
    r"""An API for todo that interacts with the config of Todo."""

    def __init__(self, bot: Red, config: Config):
        self.bot = bot
        self.config = config
        self._data: Dict[int, Dict[str, Any]] = {}
        self._pool: Pool = Pool()
        self._loop: asyncio.AbstractEventLoop = self.bot.loop

    async def delete_data(self, user_id: int) -> None:
        """|coro|

        Delete data for a user. This should only really be used when :meth:`red_delete_data_for_user` gets called

        Parameters
        ----------
        user_id: :class:`int`
            The user to clear the data for
        """
        await self.config.user_from_id(user_id).clear()
        self._data.pop(user_id, None)

    async def get_user_data(self, user_id: int) -> Dict[str, Any]:
        """|coro|

        Get a user's data from the cache. This is preferred over grabbing it directly from the cache

        Arguments
        ---------
        user_id: :class:`int`
            The id of the user to grab data for

        Raises
        ------
        TypeError
            The user type was not an int

        Returns
        -------
        :class:`dict`
            The user's data
        """
        if not isinstance(user_id, int):
            raise TypeError(f"User id must be 'int' not {user_id.__class__!r}")
        if user_id not in self._data.keys():
            await self._load_items(user=user_id)
        return self._data[user_id]

    async def get_user_item(self, user: User, key: str) -> Any:
        """|coro|

        Get an item from a user's config

        Arguments
        ---------
        user: :class:`int`|:class:`User`|:class:`Member`
            The user to grab the item from
        key: :class:`str`
            The key to get

        Returns
        -------
        Any
            The item from the user's config

        Raises
        ------
        KeyError
            The key was not in the user's config
        """
        user = self._get_user(user)
        data = await self.get_user_data(user)
        return data[key]

    async def get_todo_from_index(
        self, user: User, index: int, completed: bool = False
    ) -> Optional[Union[Dict[str, Any], str]]:
        """|coro|

        Get a todo from a user's id

        Arguments
        ---------
        user: :class:`int`|:class:`User`|:class:`Member`
            The user from which you are getting the todo
        index: :class:`int`
            The index of the todo
        completed: Optional[:class:`bool`]
            Whether to get from the completed list or the todo list. Defaults to False (grabbing from todos)

        Raises
        ------
        IndexError
            The index was out of range

        Returns
        ------
        Union[dict, str]
            The todo dictionary or the completed task
        """
        user = self._get_user(user)
        data = await self.get_user_data(user)
        key = "todos"
        if completed:
            key = "completed"
        if not data.get(key):
            return None
        return data.get(key)[index]  # type:ignore

    async def _load_items(self, *, user: int = None) -> None:
        """|coro|

        An internal method to load the data into the cache.
        Optionally, you can load a user's data into the cache

        Arguments
        ---------
        user: :class:`int`
            This is not required. The user to load the items into the cache

        Raises
        ------
        TypeError
            The user was not an integer"""
        if user is not None and not isinstance(user, int):
            raise TypeError(f"User must be int not {user.__class__!r}")
        if not user:
            self._data = await self.config.all_users()
            return
        self._data[user] = await self.config.user_from_id(user).all()

    async def set_user_item(self, user: User, key: str, data: Any, *, fix: bool = True) -> None:
        """|coro|

        Save a user item via key

        Arguments
        ---------
        user: :class:`int`|:class:`User`|:class:`Member`
            The user you are saving the data for
        data: :class:`Any`
            Data that's being saved

        Raises
        ------
        KeyError
            The key was not found in the user's settings

        See :meth:`get_user_data` for more
        """
        user = self._get_user(user)
        if key not in config_structure.keys():
            raise KeyError(f"'{key}' is not a registered value or group")
        await self.config.user_from_id(user).set_raw(key, value=data)
        await self._load_items(user=user)
        if key == "todos" and fix:
            await self._maybe_fix_todos(user)

    async def set_user_data(self, user: User, data: Dict[str, Any]) -> None:
        """|coro|

        Sets a user's data. NOTE This should probably not be used as it can break a user's config

        Arguments
        ---------
        user: :class:`int`|:class:`User`|:class:`Member`
            The user to set the data of
        data: :class:`dict`
            The data to save to the user's config
        """
        user = self._get_user(user)
        await self.config.user_from_id(user).set(data)
        await self._load_items(user=user)
        await self._maybe_fix_todos(user)

    async def set_user_setting(self, user: User, key: str, setting: Any) -> None:
        """|coro|

        Set a setting for a user

        Arguments
        ---------
        user: :class:`int`|:class:`User`|:class:`Member`
            The user that the setting is being set for
        key: :class:`str`
            The actual setting to be set
        setting: :class:`Any`
            The value for the setting

        Raises
        ------
        KeyError
            The key was not in the user's settings
        """
        user = self._get_user(user)
        data = await self.get_user_item(user, "user_settings")
        if key not in config_structure["user_settings"].keys():  # type:ignore
            raise KeyError(f"'{key}' was not in the user's settings")
        data[key] = setting
        await self.set_user_item(user, "user_settings", data)

    async def get_user_setting(self, user: User, key: str) -> Any:
        """|coro|

        Get a setting of a user

        Arguments
        ---------
        user: :class:`int`|:class:`User`|:class:`Member`
            The user to get the setting from
        key: :class:`str`
            The setting to get

        Returns
        -------
        Any
            The setting's value

        Raises
        ------
        KeyError
            The key was not in the user's settings
        """
        user = self._get_user(user)
        data = await self.get_user_item(user, "user_settings")
        return data[key]

    @staticmethod
    def _get_user(user: User) -> int:
        """An internal function to get a user id based off of the type"""
        return user if isinstance(user, int) else user.id

    async def _maybe_autosort(self, user: Union[discord.Member, discord.User]) -> None:
        """An internal function to maybe autosort todos"""

        # Okay, so I modified this a bit just for a few reasons
        # A) Todos need to be "sorted" by pinned todos as otherwise the indexes won't match up
        # B) I hate myself

        data = await self.get_user_data(user.id)
        todos = await self._maybe_fix_todos(user.id)
        completed = data["completed"]
        if not any([completed, todos]):
            return
        settings = data["user_settings"]
        reverse = settings["reverse_sort"]
        autosort = settings["autosorting"]

        if todos:
            pinned = []
            extra = []
            for todo in todos:
                if todo["pinned"]:
                    pinned.append(todo)
                else:
                    extra.append(todo)
            if autosort:
                pinned.sort(key=lambda x: x["task"], reverse=reverse)
                extra.sort(key=lambda x: x["task"], reverse=reverse)
            todos = pinned
            todos.extend(extra)
        if completed and autosort:
            completed.sort(reverse=reverse)

        data["completed"] = completed
        data["todos"] = todos
        await self.set_user_data(user, data)

    async def _maybe_fix_todos(self, user_id: int):
        """Scan todos and fix the fucked ones"""
        data = await self.get_user_item(user_id, "todos")
        if not data:
            return
        elif not isinstance(data, list):
            # Super fucked todos
            await self.set_user_item(user_id, "todos", [], fix=False)
            return
        fixer: List[Tuple[int, dict]] = []
        for num, todo in enumerate(data):
            if not isinstance(todo, dict):
                payload = {"task": todo, "pinned": False, "timestamp": None}
                fixer.append((num, payload))
                continue
            if not todo.get("pinned"):
                todo["pinned"] = False
                fixer.append((num, todo))
                continue
            if (ts := todo.get("timestamp")) and not isinstance(ts, int):  # type:ignore
                try:
                    ts = int(ts)
                except ValueError:
                    ts = None
                todo["timestamp"] = ts
                fixer.append((num, todo))
        for index, payload in fixer:
            try:
                data.pop(index)
            except IndexError:
                pass
            else:
                data.insert(index, payload)
        await self.set_user_item(user_id, "todos", data, fix=False)
        return data

    async def query_list(self, user: User, *, regex: bool, query: str) -> List[Dict[str, str]]:
        uid = self._get_user(user)

        async def method(t: Dict[str, Any]) -> bool:
            task = t["task"]
            if regex:
                passed, worked = await self._safe_regex(query, task)
                if not passed:
                    raise InvalidRegex
                return worked
            return query in task

        todos = await self.get_user_item(uid, "todos")
        return [x async for x in async_filter(method, todos)]

    async def _safe_regex(self, regex: str, item: str) -> Tuple[bool, bool]:
        # I got this from TrustyJAID's retrigger cog, which is licensed under MIT
        # here is the source for that method:
        # https://github.com/TrustyJAID/Trusty-cogs/blob/master/retrigger/triggerhandler.py#L507-#L552
        # This is licensed under MIT which you can find here:
        # https://github.com/TrustyJAID/Trusty-cogs/blob/master/LICENSE.txt
        try:
            process = self._pool.apply_async(re.search, (regex, item))
            task = functools.partial(process.get, timeout=2.0)
            new_task = await self._loop.run_in_executor(None, task)
            search = await asyncio.wait_for(new_task, timeout=20.0)
        except mp.TimeoutError:
            log.debug("Regex processing took too long.")
            return False, False
        except asyncio.TimeoutError:
            log.debug("Regex asycnio took too long.")
            return False, False
        except ValueError as e:
            log.error("Value error in `_safe_regex`:", exc_info=e)
            return False, False
        except Exception as e:
            log.error("General exception in `_safe_regex`:", exc_info=e)
            return True, False  # Not gonna return this tbh
        else:
            return True, search
