# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

from dataclasses import dataclass

__all__ = ["User"]

@dataclass(frozen=True)
class User:
    intelligence: int
    strength: int
    agility: int
    determination: int

    __slots__ = ("intelligence", "strength", "agility", "determination")

    def to_json(self):
        return {
            x: getattr(self, x) for x in self.__slots__
        }

    @property
    def has_max_stats(self) -> bool:
        return all([getattr(self, x) == 50 for x in self.__slots__])

    @has_max_stats.setter
    def has_max_stats(self, *args):
        raise RuntimeError("You cannot set this lmfao")
