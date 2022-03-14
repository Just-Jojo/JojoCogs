from typing import Any, Dict, Final

__all__ = ["__author__", "__suggestors__", "__version__", "config_structure"]

__authors__ = ["Jojo#7791"]
__suggestors__ = ["Blackbird#0001", "EVOLVE#8888", "skylarr#6666", "kato#0666", "MAX#1000"]
__version__ = "3.0.24"
config_structure: Final[Dict[str, Any]] = {
    "todos": [],  # List[Dict[str, Any]] "task": str, "pinned": False
    "completed": [],  # List[str]
    "managers": [],  # List[int] Discord member id's
    "user_settings": {
        "autosorting": False,
        "colour": None,
        "combine_lists": False,
        "completed_emoji": None,
        "completed_category_emoji": None,
        "extra_details": False,
        "number_todos": True,
        "pretty_todos": False,
        "private": False,
        "reverse_sort": False,
        "todo_emoji": None,
        "todo_category_emoji": None,
        "use_embeds": True,
        "use_markdown": False,
        "use_timestamps": False,
    },
}
