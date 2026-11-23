from current_line import current_line
from copy import deepcopy
from os import name
from typing import Generator

from typeguard import typechecked as typecheck
from runtime_data import FunctionDefinitionsToTurnIntoInstructions
import utils

from ast_ import (
    Block,
    ClassDef,
    ClassReturn,
    Deref,
    Expression,
    FieldAccess,
    FunctionCall,
    FunctionDef,
    Ident,
    New,
    Number,
    Operation,
    Pointer,
    Program,
    ReturnStmt,
    ScopeInfo,
    String,
    Type,
    Variable,
)


@typecheck
def getVariable(ident: Ident, scopeInfo: ScopeInfo|None) -> tuple[Variable, ScopeInfo]:
    assert scopeInfo, f"Cannot resolve variable {utils.cyan(ident.name)}: no enclosing scope"
    match scopeInfo.scope:
        case Block(statements):
            for i, stmt in enumerate(statements[:scopeInfo.stmtIndex]):
                match stmt:
                    case Variable(name):
                        if name == ident.name:
                            return (stmt, ScopeInfo(scopeInfo.scope, i))
        case FunctionDef(params=params):
            for param in params:
                if param.name == ident.name:
                    return (param, scopeInfo)
        case Program():
            for stmt in scopeInfo.scope.symbols:
                match stmt:
                    case Variable(name):
                        if name == ident.name:
                            return (stmt, scopeInfo)
            raise NameError(f"Unknown variable {utils.cyan(ident.name)}")
    return getVariable(ident, scopeInfo.scope.parent_positioning)



@typecheck
def getClass(name: str, scopeInfo: ScopeInfo) -> tuple[ClassDef, ScopeInfo]:
    clsVar, clsVarsScopeInfo = getVariable(Ident(name), scopeInfo)
    assert isinstance(clsVar.defaultValue, ClassDef)
    return clsVar.defaultValue, clsVarsScopeInfo 


@typecheck
def getExpressionSize(expression: Expression, scopeInfo: ScopeInfo):
    return getTypeSize(getExpressionType(expression, scopeInfo), scopeInfo)
@typecheck
def getTypeSize(type: Type, scopeInfo: ScopeInfo):
    match type:
        case Type("void"):
            return 0
        case Type("int"):
            return 1
        case Type("pointer"):
            return 1 #temp hack because we store a MemSlot in that spot
        case Type("function", subtypes):
            return sum(map(lambda type_: getTypeSize(type_, scopeInfo), subtypes[:-1]))
        case Type("class", subtypes):
            clsVar, clsesScope = getVariable(Ident(type.subtypes[0].name ), scopeInfo)
            cls = clsVar.defaultValue
            assert isinstance(cls, ClassDef)
            total = 0
            for field in cls.fields:
                total+=getTypeSize(field.type_, clsesScope)
            return total
        case _:
            raise TypeError(f"Cannot determine storage size for type {type}")

@typecheck
def isPointingToClass(functionReference: Expression, scopeInfo: ScopeInfo):
    var_, scopeInfo = getVariable(functionReference, scopeInfo)
    return var_.type_.name == "class"
@typecheck
def getExpressionType(expression: Expression, scopeInfo: ScopeInfo) -> Type:
    match expression:
        case New():
            innerType = getExpressionType(expression.expression, scopeInfo)
            return Type("pointer", subtypes=[innerType])
        case Number():
            return Type("int")
        case String():
            return Type("string")
        case Operation(op=op, left=left, right=right):
            left_type = getExpressionType(left, scopeInfo)
            right_type = getExpressionType(right, scopeInfo)
            assert left_type == right_type, (
                f"Operator {utils.cyan(op)} requires matching operand types: "
                f"left is {left_type}, right is {right_type} "
                f"for operands {left!r} and {right!r}"
            )
            return left_type
        case Ident(name):
            if name == "void":
                return Type("void")
            var_, scopeInfo = getVariable(expression, scopeInfo)
            #potential bug
            return var_.type_
        case Pointer():
            return Type("pointer", [getExpressionType(expression.pointsTo, scopeInfo)])
        case FieldAccess():
            type_ = getExpressionType(expression.object, scopeInfo)
            if type_.name == "pointer":
                assert type_.subtypes[0].name == "class"
                cls, _ = getClass(type_.subtypes[0].subtypes[0].name, scopeInfo)
            else:
                assert type_.name == "class"
                cls, _ = getClass(type_.subtypes[0].name, scopeInfo)
            assert isinstance(cls, ClassDef), f"{cls} is not ClassDef"
            field = cls.getField(expression.fieldName)
            return field.type_
        case Deref():
            pointerType = getExpressionType(expression.pointer, scopeInfo)
            assert pointerType.name == "pointer"
            return pointerType.subtypes[0]
        case FunctionDef():
            return Type("function", list(map(lambda param: param.type_ , (expression.params)))+[expression.ReturnType])
        case FunctionCall():
            if isPointingToClass(expression.functionReference, scopeInfo):
                var_, scopeInfo = getVariable(expression.functionReference, scopeInfo)
                return Type("class", [Type(var_.name)])
                # cls = var_.defaultValue

            functionDef, _ = resolveFunctionReferenceToDefinition(expression.functionReference, scopeInfo)
            return functionDef.ReturnType

        case _:
            raise TypeError(f"Cannot determine type of expression {expression!r}")


def iterReturnStmts(block: Block) -> Generator[tuple[ReturnStmt, ScopeInfo]]:
    for i, stmt in enumerate(block.statements):
        match stmt:
            case ReturnStmt():
                yield (stmt, ScopeInfo(block, i))
            case Block():
                yield from iterReturnStmts(stmt)





#####
def resolveFunctionReferenceToDefinition(functionReference: Expression, scopeInfo: ScopeInfo) -> tuple[FunctionDef, ScopeInfo]:
    assert isinstance(functionReference, Ident), (
        f"Function call requires a named function, got {functionReference!r}"
    )
    var_, scopeInfo = getVariable(functionReference, scopeInfo)
    assert isinstance(scopeInfo.scope, Program), (
        f"Function {utils.cyan(functionReference.name)}: only calls to global functions "
        f"are supported; found in {type(scopeInfo.scope).__name__} scope"
    )
    assert isinstance(var_, Variable), (
        f"Function {utils.cyan(functionReference.name)}: expected a variable definition, got {var_!r}"
    )
    if isinstance(var_.defaultValue, ClassDef):
        cls = var_.defaultValue
        functionDef = FunctionDef(params=deepcopy(cls.fields), ReturnType=Type("class", [Type(var_.name)]), body=Block([
            ClassReturn(range=functionReference.range, created_at=current_line())
        ]), parent_positioning=cls.parent_positioning, isConstructor=True)
        FunctionDefinitionsToTurnIntoInstructions.append(functionDef)
    else:
        functionDef = var_.defaultValue
    assert isinstance(functionDef, FunctionDef), (
        f"Cannot call {utils.cyan(functionReference.name)}: expected a function, "
        f"got variable of type {var_.type_} with value {functionDef!r}"
    )
    return functionDef, scopeInfo
