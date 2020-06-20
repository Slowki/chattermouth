import enum


class Category(enum.Enum):
    """Categories for text classification."""

    YES: str = "YES"
    NO: str = "NO"
    QUESTION: str = "QUESTION"


#: A set of all categories.
CATEGORIES = frozenset(Category)
