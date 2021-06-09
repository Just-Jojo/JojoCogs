# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT


class APIError(Exception):
    def __init__(self):
        super().__init__("There was something wrong with that method.")
