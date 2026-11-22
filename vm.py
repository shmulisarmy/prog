from copy import deepcopy
from dataclasses import dataclass, field
import operator

from ast_ import ClassReturn
from builtInFunctions import BuiltInFunction, builtInFunctions
from heap import Heap
from instructions import Allocate, Dup, OffsetPointer, BinaryOperation, CallFunctionWithParamStackSize, DerefInstruction, Instruction, JumpIfZero, LoadMemoryFromSlot, PlaceAbsoluteMemSlotOnStack, PlaceStackMemoryIntoMemslotOnStack, PlaceStackMemoryIntoSlot, PushNumber, ReturnInstruction
from runtime_data import FunctionInstructionStartLocations, functionInstructions, FunctionStackBumpSize
from runtime_data_types import MemLocationKind, MemSlot


OPERATIONS = {
    "+": operator.add,
    "<": operator.lt,
    ">": operator.gt,
    "-": operator.sub,
    "*": operator.mul,
    "/": operator.truediv,
    "//": operator.floordiv,
    "%": operator.mod,
}



@dataclass
class Stackframe:
    stackLocalMemLocationStart: int
    InstructionReturnAdrress: int|None

@dataclass
class Vm:
    instructions: list[Instruction]
    stack: list[int | float] = field(default_factory=list)
    stackframes: list[Stackframe] = field(default_factory=list)
    instructionPtr = 0
    heap: Heap = field(default_factory=Heap)
    def __post_init__(self):
        
        self.instructionPtr = len(self.instructions)
        
    def currentFrame(self):
        return self.stackframes[-1]

    def execute(self) -> list[int | float]:
        self.stack = []
        while self.instructionPtr < len(self.instructions):
            instruction = functionInstructions[self.instructionPtr]
            self.instructionPtr+=1
            match instruction:
                case PushNumber(value):
                    self.stack.append(value)
                case ReturnInstruction():
                    recentFrame = self.stackframes.pop()
                    memoryToReturn = self.stack[-instruction.Expressionsize:] if instruction.Expressionsize else []
                    self.stack[recentFrame.stackLocalMemLocationStart:] = []
                    self.stack.extend(memoryToReturn)
                    self.instructionPtr = recentFrame.InstructionReturnAdrress
                case ClassReturn():
                    recentFrame = self.stackframes.pop()
                    self.instructionPtr = recentFrame.InstructionReturnAdrress
                case BuiltInFunction():
                    builtInFunctions[instruction.name](self)
                case CallFunctionWithParamStackSize():
                    functionId = self.stack.pop()
                    self.stackframes.append(Stackframe(len(self.stack)-instruction.paramStackSize, self.instructionPtr))
                    self.instructionPtr = FunctionInstructionStartLocations[functionId]
                    self.stack.extend([None] * (FunctionStackBumpSize[functionId]-instruction.paramStackSize))
                case LoadMemoryFromSlot(slot):
                    match slot.memLocationKind:
                        case MemLocationKind.local_:
                            source = self.currentFrame().stackLocalMemLocationStart + slot.memOffset
                            self.stack.extend(self.stack[source:source+slot.size])
                        case MemLocationKind.global_:
                            self.stack.extend(self.stack[slot.memOffset:slot.memOffset+slot.size])
                        case MemLocationKind.NA:
                            raise
                case DerefInstruction():
                    absoluteMemSlot = self.stack.pop()
                    assert isinstance(absoluteMemSlot, MemSlot)
                    assert instruction.size == absoluteMemSlot.size
                    match absoluteMemSlot.memLocationKind:
                        case MemLocationKind.heap:
                            mem = self.heap.read(absoluteMemSlot)
                            self.stack.extend(mem)
                        case MemLocationKind.AbsoluteStackPosition:
                            mem = self.stack[absoluteMemSlot.memOffset:instruction.size]
                            self.stack.extend(mem)
                        case _:
                            raise Exception(f"not handling {absoluteMemSlot.memLocationKind} yet")
                case PlaceAbsoluteMemSlotOnStack(memSlot):
                    if memSlot.memLocationKind != MemLocationKind.local_:
                        raise
                    offset = self.currentFrame().stackLocalMemLocationStart+memSlot.memOffset
                    self.stack.append(MemSlot(offset, MemLocationKind.AbsoluteStackPosition, memSlot.size))
                case JumpIfZero(jumpBy):
                    if self.stack.pop() == 0:
                        self.instructionPtr+=jumpBy
                case PlaceStackMemoryIntoSlot(slot):
                    assert slot.memLocationKind == MemLocationKind.local_, f"we dont handle {slot.memLocationKind} yet"
                    start = self.currentFrame().stackLocalMemLocationStart + slot.memOffset
                    source = len(self.stack) - slot.size
                    self.stack[start:start + slot.size] = self.stack[source:]
                    del self.stack[source:]
                case PlaceStackMemoryIntoMemslotOnStack(size):
                    memslot = self.stack.pop()
                    assert isinstance(memslot, MemSlot)
                    assert memslot.size
                    assert memslot.size == size, f"{memslot.size} != {size}"
                    match memslot.memLocationKind:
                        case MemLocationKind.heap:
                            source = len(self.stack) - memslot.size
                            self.heap.write(memslot, self.stack[source:])
                            del self.stack[source:]
                        case MemLocationKind.AbsoluteStackPosition:
                            source = len(self.stack) - memslot.size
                            self.stack[memslot.memOffset: memslot.memOffset + memslot.size] = self.stack[source:]
                            del self.stack[source:]
                        case _:
                            raise Exception(f"we dont handle {memslot.memLocationKind} yet")
                    if instruction.keepSlotAround:
                        self.stack.append(memslot)

                case OffsetPointer(offset, size):
                    pointer = self.stack[-1]
                    assert isinstance(pointer, MemSlot)
                    self.stack[-1] = MemSlot(
                        memOffset=pointer.memOffset + offset,
                        memLocationKind=pointer.memLocationKind,
                        size=size,
                    )
                case Dup():
                    self.stack.append(deepcopy(self.stack[-1]))
                case Allocate(size):
                    memSlot = self.heap.allocate(size)
                    self.stack.append(memSlot)
                case BinaryOperation(op):

                    if op not in OPERATIONS:
                        raise ValueError(f"Unsupported operation: {op!r}")
                    if len(self.stack) < 2:
                        raise ValueError(f"Operation {op!r} requires two stack values")
                    right = self.stack.pop()
                    left = self.stack.pop()
                    self.stack.append(OPERATIONS[op](left, right))
                case _:
                    raise TypeError(f"Unsupported instruction: {instruction!r}")
        
