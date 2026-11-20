from dataclasses import dataclass
from typing import Callable, TypeAlias



StackType: TypeAlias = list[int]
builtInFunctions: dict[str, Callable[[StackType]]] = {
    "printEntireStack": lambda stack: print(stack),
    "printNumberOnStack": lambda stack: print(stack[-1])
}

@dataclass
class BuiltInFunction:
    name: str
    
