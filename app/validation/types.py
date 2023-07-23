from enum import Enum


class Grades(str, Enum):
    """like / dislike state mashine."""
    LIKE: str = "LIKE"
    DISLIKE: str = "DISLIKE"
    INDIFF: str = "INDIFF"  # indiff as default state in db.
