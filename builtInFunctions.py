from dataclasses import dataclass
from typing import Callable, TypeAlias



StackType: TypeAlias = list[int]
builtInFunctions: dict[str, Callable[[StackType]]] = {
    "printEntireStack": lambda vm: print(vm.stack),
    "printEntireHeapMemory": lambda vm: print(vm.heap._memory),
    "printNumberOnStack": lambda vm: print(vm.stack[-1])
}

@dataclass
class BuiltInFunction:
    name: str
    
