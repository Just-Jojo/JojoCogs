# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

import logging
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Union

import discord
from emoji.unicode_codes import UNICODE_EMOJI_ENGLISH
from redbot.core import commands

log = logging.getLogger("red.jojocogs.advancedinvite.utils")

__all__ = [
    "create_doc",
    "TimestampFormats",
    "timestamp_format",
    "NoneConverter",
    "InviteNoneConverter",
    "send_button",
    "Button",
    "Component",
    "Emoji",
    "EmojiConverter",
]
NoneType = type(None)


def create_doc(default: str = None, *, override: bool = False):
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
def timestamp_format(dt: datetime = None, *, dt_format: TimestampFormats = None) -> str:
    if not dt:
        dt = datetime.now()
    if not dt_format or dt_format == TimestampFormats.DEFAULT:
        return f"<t:{int(dt.timestamp())}>"
    else:
        return f"<t:{int(dt.timestamp())}:{dt_format.value}>"


if TYPE_CHECKING:
    NoneConverter = Union[NoneType, str]
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


class Route(discord.http.Route):
    BASE = "https://discord.com/api/v8"


async def send_button(
    ctx: commands.Context, components: List["Component"], content: str = None, **kwargs
) -> discord.Message:
    """Send with a button!"""
    payload: Dict[str, Any] = {}
    state = ctx._state
    if content:
        payload["content"] = str(content)
    emb, embs = kwargs.get("embed"), kwargs.get("embeds")
    if emb and embs:
        raise TypeError("You cannot specify both 'embed' and 'embeds'")
    if emb:
        payload["embeds"] = [emb.to_dict()]
    if embs:
        payload["embeds"] = [e.to_dict() for e in embs]
    payload["components"] = [c.to_dict() for c in components]
    if al := kwargs.get("allowed_mentions"):
        if state.allowed_mentions is not None:
            payload["allowed_mentions"] = state.allowed_mentions.merge(al).to_dict()
        else:
            payload["allowed_mentions"] = al.to_dict()
    else:
        payload["allowed_mentions"] = state.allowed_mentions and state.allowed_mentions.to_dict()
    channel = kwargs.get("channel", ctx.channel)
    r = Route("POST", "/channels/{channel_id}/messages", channel_id=channel.id)
    data = await ctx.bot.http.request(r, json=payload)
    return discord.Message(state=state, channel=channel, data=data)


class Component:
    """Small container for components or something"""

    def __init__(self, buttons: List["Button"]):
        self.buttons = buttons

    def to_dict(self) -> Dict[str, Any]:
        return {"type": 1, "components": [b.to_dict() for b in self.buttons]}


class Button:
    """Small button container for stuff or something"""

    __slots__ = ("label", "style", "type", "url", "emoji")

    def __init__(self, label: str, url: str, emoji: Union["Emoji", None]):
        self.label = label
        self.style = 5
        self.type = 2
        self.url = url
        self.emoji = emoji

    def to_dict(self) -> Dict[str, Any]:
        return {
            x: getattr((y := getattr(self, x)), "to_dict", lambda: y)() for x in self.__slots__
        }


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
