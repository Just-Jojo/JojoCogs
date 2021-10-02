# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

from dataclasses import dataclass


@dataclass
class Job:
    """Data class for jobs I guess"""

    payroll: int
    name: str = "Stocker"
    description: str = "Stocker at Billy Bob's bait shop and laundromat"
    stat: str = "strength"

    __slots__ = ("name", "description", "stat", "payroll",)

    def to_json(self) -> dict:
        """Return a jsonified version of the job.

        This is for storing the data in a user's config
        """
        return {
            x: getattr(self, x) for x in self.__slots__
        }
