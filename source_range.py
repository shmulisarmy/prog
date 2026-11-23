"""Source coordinates: one-based lines/characters, exclusive range ends."""

from dataclasses import field
from runtime_types import dataclass
from utils import blue


@dataclass
class Position:
    filename: str
    line: int
    character: int


    def __repr__(self) -> str:
        return f"{self.filename}:{self.line}:{self.character}"


@dataclass
class Range:
    start: Position
    end: Position


    def __repr__(self) -> str:
        return blue(f"{self.start}-{self.end.line}.{self.end.character}")


@dataclass
class Node:
    # Compiler-created nodes may not have a source location.
    range: Range | None = field(default=None, kw_only=True, compare=False)
