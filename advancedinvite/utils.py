# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

import logging
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Union, Optional

import discord
try:
    from emoji.unicode_codes import UNICODE_EMOJI_ENGLISH
except ImportError:
    from emoji import EMOJI_DATA as UNICODE_EMOJI_ENGLISH
from redbot.core import commands

log = logging.getLogger("red.jojocogs.advancedinvite.utils")

__all__ = [
    "create_doc",
    "TimestampFormats",
    "timestamp_format",
    "NoneConverter",
    "InviteNoneConverter",
    "Emoji",
    "EmojiConverter",
]
NoneType = type(None)


def create_doc(default: Optional[str] = None, *, override: bool = False):
    """Create a docstring if you don't wanna"""

    def inner(func):
        doc = default or "No Documentation"
        if not func.__doc__ or override:
            func.__doc__ = doc
        return func

    return inner


@create_doc()
class TimestampFormats(Enum):
    DEFAULT = "f"
    LONG_DATE_TIME = "F"
    SHORT_DATE = "d"
    LONG_DATE = "D"
    SHORT_TIME = "t"
    LONG_TIME = "T"
    RELATIVE_TIME = "R"


@create_doc()
def timestamp_format(dt: Optional[datetime] = None, *, dt_format: Optional[TimestampFormats] = None) -> str:
    if not dt:
        dt = datetime.now()
    if not dt_format or dt_format == TimestampFormats.DEFAULT:
        return f"<t:{int(dt.timestamp())}>"
    else:
        return f"<t:{int(dt.timestamp())}:{dt_format.value}>"


if TYPE_CHECKING:
    NoneConverter = Optional[str]
else:
    class NoneConverter(commands.Converter):
        """A simple converter for NoneType args for commands"""

        def __init__(self, *, strict: bool = False):
            self.strict = strict

        async def convert(self, ctx: commands.Context, arg: str) -> Union[NoneType, str]:
            args = ["none"]
            if not self.strict:
                args.extend(["no", "nothing"])
            if arg.lower() in args:
                return None
            return arg


if TYPE_CHECKING:
    InviteNoneConverter = Union[NoneType, discord.Invite]
else:

    class InviteNoneConverter(NoneConverter):
        def __init__(self):
            self.strict = False

        async def convert(
            self, ctx: commands.Context, arg: str
        ) -> Union[NoneType, discord.Invite]:
            ret = await super().convert(ctx, arg)
            if ret is None:
                return ret
            return await commands.InviteConverter().convert(ctx, ret)


class Emoji:
    def __init__(self, data: Dict[str, Any]):
        self.name = data["name"]
        self.id = data.get("id", None)
        self.animated = data.get("animated", None)
        self.custom = self.id is not None

    @classmethod
    def from_data(cls, data: Union[str, Dict[str, Any]]):
        log.debug(data)
        if not data:
            return None
        if isinstance(data, str):
            return cls({"name": data})
        return cls(data)

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "id": self.id}

    def as_emoji(self) -> str:
        if not self.custom:
            return self.name
        an = "a" if self.animated else ""
        return f"<{an}:{self.name}:{self.id}>"


if TYPE_CHECKING:
    EmojiConverter = Union[Emoji, NoneType]
else:

    class EmojiConverter(commands.PartialEmojiConverter):
        async def convert(self, ctx: commands.Context, arg: str) -> Union[Emoji, NoneType]:
            if arg.lower() == "none":
                return None
            arg = arg.strip()
            data = arg if arg in UNICODE_EMOJI_ENGLISH.keys() else await super().convert(ctx, arg)
            data = getattr(data, "to_dict", lambda: data)()
            return Emoji.from_data(data)
