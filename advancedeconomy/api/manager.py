# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

import random
from .jobs import Job
from .user import User


class Manager:
    def __init__(self, job: Job, user: User):
        self._job = job
        self._user = user

    async def calculate(self):
        if self._user.has_max_stats:
            return True
