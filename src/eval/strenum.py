from enum import Enum


class StrEnum(str, Enum):
    """String-valued enum compatible with Python 3.10."""

    def __str__(self) -> str:
        return self.value
