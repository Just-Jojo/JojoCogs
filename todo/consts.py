__all__ = ["config_structure"]

config_structure = {
    "todos": [],  # List[Dict[str, Any]] "task": str, "pinned": False
    "completed": [],  # List[str]
    "managers": [],  # List[int] Discord member id's
    "user_settings": {
        "autosorting": False,
        "colour": None,
        "combine_lists": False,
        "completed_emoji": None,
        "extra_details": False,
        "number_todos": True,
        "pretty_todos": False,
        "private": False,
        "reverse_sort": False,
        "todo_emoji": None,
        "use_embeds": True,
        "use_markdown": False,
        "use_timestamps": False,
    },
}
