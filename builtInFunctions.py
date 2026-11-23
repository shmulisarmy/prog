from dataclasses import field
from source_range import Range
from runtime_types import dataclass
from typing import Callable, TypeAlias



StackType: TypeAlias = list[int]
builtInFunctions: dict[str, Callable[[StackType]]] = {
    "printEntireStack": lambda vm: print(vm.stack),
    "printEntireHeapMemory": lambda vm: print(vm.heap._memory),
    "printNumberOnStack": lambda vm: print(vm.stack[-1])
}

@dataclass
class BuiltInFunction:
    range: Range = field(kw_only=True, compare=False)
    created_at: str = field(kw_only=True, compare=False)
    name: str
    
