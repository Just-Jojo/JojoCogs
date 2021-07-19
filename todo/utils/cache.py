# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

from typing import Any, Dict, Optional, Union

import discord
from redbot.core import Config, commands
from redbot.core.bot import Red

User = Union[int, discord.Member, discord.User]
__all__ = [
    "Cache",
]


class Cache:
    r"""An "Advanced" cache for todo as the old one was just a dictionary and was hard to work with"""

    def __init__(self, bot: Red, config: Config):
        self.bot = bot
        self.config = config
        self._data: Dict[int, Dict[str, Any]] = {}

    async def delete_data(self, user_id: int):
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

    async def get_user_item(self, user: User, key: str):
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

    async def _load_items(self, *, user: int = None):
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
            self._data = await self.config.all()
            return
        self._data[user] = await self.config.user_from_id(user).all()

    async def set_user_item(self, user: User, key: str, data: Any):
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
        user_data = await self.get_user_data(user)
        if key not in user_data.keys():
            raise KeyError(f"'{key}' is not a registered value or group")
        await self.config.user_from_id(user).set_raw(key, value=data)
        await self._load_items(user=user)

    async def set_user_data(self, user: User, data: Dict[str, Any]):
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

    async def set_user_setting(self, user: User, key: str, setting: Any):
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
        if key not in data.keys():
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
