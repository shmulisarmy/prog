from dataclasses import dataclass, field
from typing import TypeAlias

from builtInFunctions import BuiltInFunction
from runtime_data_types import MemLocationKind, MemSlot
from slassReturn import ClassReturn
import utils


@dataclass
class Program:
    symbols: list[Variable]



@dataclass
class ClassDefCompilerData:
    memSlotUpto: int = 0

@dataclass
class ClassDef:
    fields: list[Variable]
    parent_positioning: ScopeInfo|None = None
    compilerData: ClassDefCompilerData = None

    def getFeild(self, name: str):
        for field in self.fields:
            if field.name == name:
                return field


@dataclass
class Number:
    number: int


@dataclass
class String:
    string: str


@dataclass
class Operation:
    op: str
    left:Expression
    right:Expression


@dataclass
class FunctionCall:
    functionReference: Expression
    args: list[Expression]


@dataclass
class FieldAccess:
    object: Expression
    fieldName: str


@dataclass
class IfStatement:
    expression: Expression
    then: Block
    else_: Block|None = None
@dataclass
class Ident:
    name: str


@dataclass
class Pointer:
    pointsTo: Expression


@dataclass
class Deref:
    pointer: Expression


@dataclass
class Variable:
    name: str
    type_: Type|None
    defaultValue: Expression|None = None
    compileTimeInfo_memSlot: MemSlot|None = None


@dataclass
class Assignment:
    left: Expression    
    right: Expression 




@dataclass
class Type:
    name: str
    subtypes: list[Type] = field(default_factory=list)


    def __str__(self) -> str:
        if not self.subtypes:
            return utils.green(self.name) 
        return f"{utils.green(self.name)}[{', '.join(map(str, self.subtypes))}]"




@dataclass
class CompilerData:
    functionRuntimeId: int|None = None
    memSlotUpto = 0
@dataclass
class FunctionDef:
    params: list[Variable]
    ReturnType: Type
    body: Block
    parent_positioning: ScopeInfo|None = None
    compilerData: CompilerData = field(default_factory=lambda:CompilerData())
    isConstructor: bool = False
    


@dataclass
class Block:
    statements: list[Statement]
    parent_positioning: ScopeInfo|None = None


@dataclass
class ReturnStmt:
    value: Expression




Statement: TypeAlias = Variable|Block|ReturnStmt|FunctionCall|BuiltInFunction|Assignment|IfStatement|ClassReturn


Expression = Number|String|Operation|FunctionCall|FieldAccess|Ident|Pointer|Deref|Variable|FunctionDef|ClassDef


Scope: TypeAlias = FunctionDef|Block|Program|ClassDef


@dataclass
class ScopeInfo:
    scope: Scope
    stmtIndex: int|None=None



