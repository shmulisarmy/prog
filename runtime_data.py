from typing import TYPE_CHECKING, TypeAlias
from instructions import Instruction



if TYPE_CHECKING:
    from ast_ import FunctionDef




globalMemBumpSlot = 0
functionIds = 1
functionInstructions: list[Instruction] = []
FunctionDefinitionsToTurnIntoInstructions: list[FunctionDef] = []
FunctionId: TypeAlias = int
FunctionInstructionStartLocations: dict[FunctionId, int] = {}
FunctionStackBumpSize: dict[FunctionId, int] = {}




