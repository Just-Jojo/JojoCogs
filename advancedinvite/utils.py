from datetime import datetime
from enum import Enum
from functools import wraps

from redbot.core import commands

__all__ = ["create_doc", "TimestampFormats", "timestamp_format", "NoneConverter"]


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
def timestamp_format(dt: datetime = None, *, dt_format: TimestampFormats = None):
    if not dt:
        dt = datetime.now()
    if not dt_format or dt_format == TimestampFormats.DEFAULT:
        return f"<t:{int(dt.timestamp())}>"
    else:
        return f"<t:{int(dt.timestamp())}:{dt_format.value}>"


class NoneConverter(commands.Converter):
    """A simple converter for NoneType args for commands"""

    def __init__(self, *, strict: bool = False):
        self.strict = strict

    async def convert(self, ctx: commands.Context, arg: str):
        args = ["none"]
        if not self.strict:
            args.extend(["no", "nothing"])
        if arg.lower() in args:
            return None
        return arg
