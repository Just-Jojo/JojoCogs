# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

# Some general utilities

from datetime import datetime
from enum import Enum

from typing import Union

__all__ = ["TimestampFormats", "timestamp_format"]


class TimestampFormats(Enum):
    DEFAULT = "f"
    LONG_DATETIME = "F"
    SHORT_DATE = "d"
    LONG_DATE = "D"
    SHORT_TIME = "t"
    LONG_TIME = "T"
    RELATIVE_TIME = "R"


def timestamp_format(
    timestamp: Union[datetime, int] = None, *, ts_format: TimestampFormats = None
) -> str:
    if timestamp is not None and not (isinstance(timestamp, int) or isinstance(timestamp, datetime)):
        raise TypeError(f"Expected an instance of int or datetime not {timestamp.__class__!r}")
    if timestamp is None:
        timestamp = datetime.utcnow()
    if isinstance(timestamp, datetime):
        timestamp = int(timestamp.timestamp())
    if ts_format is None or ts_format == TimestampFormats.DEFAULT:
        return f"<t:{timestamp}>"
    return f"<t:{timestamp}:{ts_format.value}>"
