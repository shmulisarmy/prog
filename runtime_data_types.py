from dataclasses import dataclass
from enum import Enum, auto






class MemLocationKind(Enum):
    global_ = auto()
    local_ = auto()
    AbsoluteStackPosition = auto()
    NA = auto()

@dataclass
class MemSlot:
    memOffset: int
    memLocationKind: MemLocationKind
    size: int


    def __repr__(self) -> str:
        return f"::{self.memOffset}"
