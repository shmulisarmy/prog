from dataclasses import field
from runtime_types import dataclass
from typing import TypeAlias
from source_range import Node, Position, Range

from builtInFunctions import BuiltInFunction
from runtime_data_types import MemLocationKind, MemSlot
from classReturn import ClassReturn
import utils


@dataclass
class Program(Node):
    symbols: list[Variable]



@dataclass
class ClassDefCompilerData:
    memSlotUpto: int = 0

@dataclass
class ClassDef(Node):
    fields: list[Variable]
    parent_positioning: ScopeInfo|None = None
    compilerData: ClassDefCompilerData|None = None

    def getField(self, name: str) -> Variable:
        for field in self.fields:
            if field.name == name:
                return field


@dataclass
class Number(Node):
    number: int


@dataclass
class String(Node):
    string: str


@dataclass
class Operation(Node):
    op: str
    left:Expression
    right:Expression


@dataclass
class FunctionCall(Node):
    functionReference: Expression
    args: list[Expression]


@dataclass
class FieldAccess(Node):
    object: Expression
    fieldName: str


@dataclass
class IfStatement(Node):
    expression: Expression
    then: Block
    else_: Block|None = None
@dataclass
class Ident(Node):
    name: str


@dataclass
class Pointer(Node):
    pointsTo: Expression


@dataclass
class Deref(Node):
    pointer: Expression


@dataclass
class New(Node):
    expression: Expression


@dataclass
class Variable(Node):
    name: str
    type_: Type|None
    defaultValue: Expression|None = None
    compileTimeInfo_memSlot: MemSlot|None = None


@dataclass
class Assignment(Node):
    left: Expression    
    right: Expression 




@dataclass
class Type(Node):
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
class FunctionDef(Node):
    params: list[Variable]
    ReturnType: Type
    body: Block
    parent_positioning: ScopeInfo|None = None
    compilerData: CompilerData = field(default_factory=lambda:CompilerData())
    isConstructor: bool = False
    


@dataclass
class Block(Node):
    statements: list[Statement]
    parent_positioning: ScopeInfo|None = None


@dataclass
class ReturnStmt(Node):
    value: Expression




Statement: TypeAlias = Variable|Block|ReturnStmt|FunctionCall|BuiltInFunction|Assignment|IfStatement|ClassReturn


Expression = Number|String|Operation|FunctionCall|FieldAccess|Ident|Pointer|Deref|New|Variable|FunctionDef|ClassDef


Scope: TypeAlias = FunctionDef|Block|Program|ClassDef


@dataclass
class ScopeInfo:
    scope: Scope
    stmtIndex: int|None=None



