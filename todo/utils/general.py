# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

# Some general utilities

from datetime import datetime
from enum import Enum

__all__ = ["TimestampFormats", "timestamp_format"]


class TimestampFormats(Enum):
    DEFAULT = "f"
    LONG_DATETIME = "F"
    SHORT_DATE = "d"
    LONG_DATE = "D"
    SHORT_TIME = "t"
    LONG_TIME = "T"
    RELATIVE_TIME = "R"


def timestamp_format(timestamp: datetime = None, *, ts_format: TimestampFormats = None):
    if timestamp is None:
        timestamp = datetime.utcnow()
    if ts_format is None or ts_format == TimestampFormats.DEFAULT:
        return f"<t:{int(timestamp.timestamp())}>"
    return f"<t:{int(timestamp.timestamp())}:{ts_format.value}>"
