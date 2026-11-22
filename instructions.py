from dataclasses import dataclass
from typing import TypeAlias

from builtInFunctions import BuiltInFunction
from runtime_data_types import MemSlot
from classReturn import ClassReturn


@dataclass
class PushNumber:
    value: int


@dataclass
class BinaryOperation:
    op: str


@dataclass
class CallFunctionWithParamStackSize:
    paramStackSize: int


@dataclass
class ReturnInstruction:
    Expressionsize: int

@dataclass
class PlaceStackMemoryIntoSlot:
    memSlot: MemSlot


@dataclass
class PlaceStackMemoryIntoMemslotOnStack:
    size: int
    keepSlotAround: bool = False

@dataclass
class OffsetPointer:
    offset: int
    size: int


@dataclass
class LoadMemoryFromSlot:
    memSlot: MemSlot

@dataclass
class PlaceAbsoluteMemSlotOnStack:
    memSlot: MemSlot


@dataclass
class DerefInstruction:
    size: int
@dataclass
class JumpIfZero:
    jumpBy: int


@dataclass
class Allocate:
    amount: int


@dataclass
class Dup:
    pass

Instruction: TypeAlias = PushNumber | BinaryOperation|CallFunctionWithParamStackSize|ReturnInstruction|PlaceStackMemoryIntoSlot|LoadMemoryFromSlot|ClassReturn|BuiltInFunction|PlaceAbsoluteMemSlotOnStack|DerefInstruction|PlaceStackMemoryIntoMemslotOnStack|OffsetPointer|Allocate|Dup
