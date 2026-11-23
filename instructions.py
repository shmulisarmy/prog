from dataclasses import field
from source_range import Range
from ast_ import ClassDef
from sizeOf import SizeOf
from runtime_types import dataclass
from typing import TypeAlias

from builtInFunctions import BuiltInFunction
from runtime_data_types import MemSlot
from classReturn import ClassReturn


@dataclass
class PushNumber:
    range: Range = field(kw_only=True, compare=False)
    created_at: str = field(kw_only=True, compare=False)
    value: int


@dataclass
class BinaryOperation:
    range: Range = field(kw_only=True, compare=False)
    created_at: str = field(kw_only=True, compare=False)
    op: str


@dataclass
class CallFunctionWithParamStackSize:
    paramStackSize: int|SizeOf
    range: Range = field(kw_only=True, compare=False)
    created_at: str = field(kw_only=True, compare=False)


@dataclass
class ReturnInstruction:
    range: Range = field(kw_only=True, compare=False)
    created_at: str = field(kw_only=True, compare=False)
    ExpressionSize: int|SizeOf

@dataclass
class PlaceStackMemoryIntoSlot:
    range: Range = field(kw_only=True, compare=False)
    created_at: str = field(kw_only=True, compare=False)
    memSlot: MemSlot


@dataclass
class PlaceStackMemoryIntoMemslotOnStack:
    range: Range = field(kw_only=True, compare=False)
    created_at: str = field(kw_only=True, compare=False)
    size: int|SizeOf
    keepSlotAround: bool = False


@dataclass
class OffsetOfField:
    cls: ClassDef
    field: str

@dataclass
class OffsetPointer:
    range: Range = field(kw_only=True, compare=False)
    created_at: str = field(kw_only=True, compare=False)
    offset: int|OffsetOfField
    newSize: int|SizeOf


@dataclass
class LoadMemoryFromSlot:
    range: Range = field(kw_only=True, compare=False)
    created_at: str = field(kw_only=True, compare=False)
    memSlot: MemSlot

@dataclass
class PlaceAbsoluteMemSlotOnStack:
    range: Range = field(kw_only=True, compare=False)
    created_at: str = field(kw_only=True, compare=False)
    memSlot: MemSlot


@dataclass
class DerefInstruction:
    range: Range = field(kw_only=True, compare=False)
    created_at: str = field(kw_only=True, compare=False)
    size: int|SizeOf
@dataclass
class JumpIfZero:
    range: Range = field(kw_only=True, compare=False)
    created_at: str = field(kw_only=True, compare=False)
    jumpBy: int



@dataclass
class Allocate:
    range: Range = field(kw_only=True, compare=False)
    created_at: str = field(kw_only=True, compare=False)
    amount: int|SizeOf


@dataclass
class Dup:
    range: Range = field(kw_only=True, compare=False)
    created_at: str = field(kw_only=True, compare=False)
    pass

Instruction: TypeAlias = PushNumber | BinaryOperation|CallFunctionWithParamStackSize|ReturnInstruction|PlaceStackMemoryIntoSlot|LoadMemoryFromSlot|ClassReturn|BuiltInFunction|PlaceAbsoluteMemSlotOnStack|DerefInstruction|PlaceStackMemoryIntoMemslotOnStack|OffsetPointer|Allocate|Dup|JumpIfZero
