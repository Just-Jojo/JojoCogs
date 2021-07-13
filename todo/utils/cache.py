# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

from typing import Any, Dict, Optional, Union

import discord

import json
import asqlite

from redbot.core.data_manager import cog_data_path

User = Union[int, discord.Member, discord.User]
__all__ = [
    "Cache",
]


CREATE_TABLE = """CREATE TABLE IF NOT EXISTS todo (
    user_id INT PRIMARY KEY,
    todos TEXT NOT NULL,
    completed TEXT NOT NULL,
    user_settings TEXT NOT NULL
);
"""
_keys = {
    "todos": [],
    "completed": [],
    "user_settings": {
        "autosorting": False,
        "colour": None,
        "combine_lists": False,
        "extra_details": False,
        "number_todos": True,
        "pretty_todos": False,
        "private": False,
        "reverse_sort": False,
        "use_embeds": False,
        "use_markdown": False,
        "use_timestamps": False,
    }
}
CREATE_USER_DATA = """INSERT INTO todo VALUES (?, ?, ?, ?)"""
SELECT_DATA = """SELECT todos, completed, user_settings FROM todo WHERE user_id = ?"""
UPDATE_USER = """UPDATE todo
SET todos = ?, completed = ?, user_settings = ?
WHERE user_id = ?
"""


class Cache:
    def __init__(self):
        self._connection: asqlite.Connection
        self._cursor: asqlite.Cursor
        self._started = False
        self._data = {}

    @classmethod
    async def init(cls, cog):
        self = cls()
        data_path = cog_data_path(cog)
        self._connection = await asqlite.connect(f"{data_path}/test.db")
        self._cursor = await self._connection.cursor()
        await self._fill_cache()
        return self

    async def teardown(self):
        await self._cursor.close()
        await self._connection.close()

    async def _fill_cache(self, *, user_id: int = None):
        if not self._started:
            await self._cursor.execute(CREATE_TABLE)
            await self._connection.commit()
            self._started = True

        if user_id:
            if not isinstance(user_id, int):
                raise TypeError(f"'user_id' must be type int not {user_id.__class__!r}")
            await self._cursor.execute(SELECT_DATA, user_id)
            data = await self._cursor.fetchone()
            payload = {}
            for key, value in zip(_keys.keys(), data):
                payload[key] = json.loads(value)
            self._data[user_id] = payload
            return
        await self._cursor.execute("SELECT * FROM todo")
        data = await self._cursor.fetchall()
        for row in data:
            row = list(row)
            uid = row.pop(0)
            self._data[uid] = {}
            for key, value in zip(_keys.keys(), row):
                value = json.loads(value)
                self._data[uid][key] = value

    async def set_user_data(self, user: User, data: dict):
        uid = self._get_uid(user)
        if not data.keys() == _keys.keys():
            raise ValueError("The payload's keys must be equal to the default's keys")
        payload = [json.dumps(value) for value in data.values()]
        payload.append(uid)
        await self._cursor.execute(UPDATE_USER, *payload)
        await self._connection.commit()
        await self._fill_cache(user_id=uid)

    async def set_user_item(self, user: User, key: str, data: Any):
        uid = self._get_uid(user)
        payload = await self.get_user_data(uid)
        payload[key] = data
        await self.set_user_data(uid, payload)

    async def set_user_setting(self, user: User, key: str, data: Any):
        uid = self._get_uid(user)
        payload = await self.get_user_item(uid, "user_settings")
        payload[key] = data
        await self.set_user_item(uid, "user_settings", payload)

    async def get_user_data(self, user: Union[User]):
        uid = self._get_uid(user)
        if uid not in self._data.keys():
            data = [uid] + [json.dumps(v) for v in _keys.values()]
            print(0 in data)
            await self._cursor.execute(CREATE_USER_DATA, *data)
            await self._connection.commit()
            await self._fill_cache(user_id=uid)
        return self._data[uid]

    async def get_user_item(self, user: User, key: str):
        uid = self._get_uid(user)
        data = await self.get_user_data(uid)
        return data[key]

    async def get_user_setting(self, user: User, setting: str):
        uid = self._get_uid(user)
        data = await self.get_user_item(uid, "user_settings")
        return data[setting]

    async def get_todo_from_index(self, user: User, index: int):
        uid = self._get_uid(user)
        data = await self.get_user_item(uid, "todos")
        return data[index]

    def _get_uid(self, user_or_id: User):
        return user_or_id if isinstance(user_or_id, int) else user_or_id.id
