import json
import pathlib

from .better_blacklist import setup  # type:ignore[attr-defined]

with open(pathlib.Path(__file__).parent / "info.json") as fp:
    __red_end_user_data_statement__ = json.load(fp)["end_user_data_statement"]
