"""
MIT License

Copyright (c) 2021 Jojo#7711

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import logging
from abc import ABC
from typing import Union

import discord
from redbot.core import Config, commands
from redbot.core.bot import Red


class ToDoMixin(ABC):
    """Mixin allowing for easier type hints"""

    @commands.group()
    async def todo(self, ctx):
        raise NotImplementedError

    def __init__(self, *_args):
        self.config: Config
        self.bot: Red
        self.log: logging.Logger
        self._no_completed_message: str
        self._no_todo_message: str
        self._failure_explanation: str

    async def _get_user_config(
        self, user: Union[str, discord.User, discord.Member]
    ) -> dict:
        ...

    async def _get_destination(self, ctx: commands.Context) -> discord.TextChannel:
        ...


class CompositeMetaclass(type(commands.Cog), type(ABC)):
    """Metaclass so it doesn't break or something idk"""

    pass
