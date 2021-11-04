# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

from typing import List

__all__ = ["_format_todos", "_format_completed", "_build_underline"]


def _build_underline(data: str, md: bool = False, emoji: bool = False) -> str:
    """An internal function to return a rough estimate of an underline"""
    add = 3
    if md and not emoji:
        add = 0
    elif emoji and not md:
        add = 7
    elif emoji and md:
        add = 1
    return "\n" + "-" * (len(data) + add)


async def _format_todos(pinned: List[str], other: List[str], **settings) -> List[str]:
    """An enternal function to format a user's todos"""
    pretty = settings.get("pretty_todos", False)
    use_md = settings.get("use_markdown", False)
    number = settings.get("number_todos", False)
    emoji = (
        settings.get("todo_emoji", "\N{LARGE GREEN SQUARE}")
        if not use_md
        else "\N{LARGE GREEN SQUARE}"
    )
    emoji = emoji or "\N{LARGE GREEN SQUARE}"
    fmt = "" if use_md else "**"
    should_insert = len(pinned) > 0
    should_insert_todos = len(other) > 0
    to_insert = (
        len(pinned) + 1
    )  # This gives me back the last index + 1 allowing me to insert the "other todos" into it
    pinned.extend(other)
    ret = []
    for num, task in enumerate(pinned, 1):
        if number:
            task = f"{num}. {task}"
        if pretty:
            task = f"{emoji} {task}"
        ret.append(task)
    if should_insert:
        ret.insert(
            0,
            f"\n\N{PUSHPIN} {fmt}Pinned todos{fmt}"
            + _build_underline("📌 Pinned todos", use_md, True),
        )
        if should_insert_todos:
            ret.insert(
                to_insert,
                f"\n\N{RADIO BUTTON} {fmt}Other todos{fmt}"
                + _build_underline("🔘 Other todos", use_md, True),
            )
    else:
        ret.insert(
            0,
            f"\N{RADIO BUTTON} {fmt}Todos{fmt}" + _build_underline("🔘 Todos", use_md, True),
        )
    return ret


async def _format_completed(completed: List[str], combined: bool = False, **settings) -> List[str]:
    pretty = settings.get("pretty_todos")
    number = settings.get("number_todos")
    use_md = settings.get("use_markdown")
    fallback = "\N{WHITE HEAVY CHECK MARK}"
    completed_emoji: str = settings.get("completed_emoji", fallback) if not use_md else fallback
    completed_emoji = completed_emoji or fallback  # Sometimes this is none which is annoying
    fmt = "" if settings.get("use_markdown") else "**"
    ret = []
    for num, task in enumerate(completed, 1):
        if number:
            task = f"{num}. {task}"
        if pretty:
            task = f"{completed_emoji} {task}"
        ret.append(task)
    if combined:
        emoji = "✅" if use_md else "☑"
        data = f"{emoji} Completed todos"
        ret.insert(
            0,
            f"\n\N{BALLOT BOX WITH CHECK}\N{VARIATION SELECTOR-16} {fmt}Completed todos{fmt}"
            + _build_underline(data, use_md, True),  # type:ignore
        )
    return ret
