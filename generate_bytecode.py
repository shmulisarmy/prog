
from copy import deepcopy
from dataclasses import dataclass
import re
from typing import TypeAlias

from typeguard import typechecked
from ast_ import Assignment, Block, ClassDef, ClassReturn, Deref, Expression, FieldAccess, FunctionCall, FunctionDef, Ident, IfStatement, Number, Operation, Pointer, Program, ReturnStmt, ScopeInfo, Statement, Type, Variable
from builtInFunctions import BuiltInFunction
from compilerTools import getClass, getExpressionSize, getExpressionType, getTypeSize, getVariable, resolveFunctionReferenceToDefinition
from instructions import OffsetPointer, BinaryOperation, CallFunctionWithParamStackSize, DerefInstruction, Instruction, JumpIfZero, LoadMemoryFromSlot, PlaceAbsoluteMemSlotOnStack, PlaceStackMemoryIntoMemslotOnStack, PlaceStackMemoryIntoSlot, PushNumber, ReturnInstruction
import instructions
import runtime_data
from runtime_data_types import MemLocationKind, MemSlot





varName: TypeAlias = str
Size: TypeAlias = int
def makeFunctionByteCode(function: FunctionDef, scopeInfo: ScopeInfo, isFromConstructor = False) -> list[Instruction]:
    instructions: list[Instruction] = []
    for param in function.params:
        instructions.extend(makeStatementByteCode(param, ScopeInfo(function), isFromConstructor=isFromConstructor))
    instructions.extend(makeBlockByteCode(function.body, ScopeInfo(FunctionDef, 0)))
    # as we make turn the function into instructions we also dedicate memory slots to params and vars 
    runtime_data.FunctionStackBumpSize[function.compilerData.functionRuntimeId] = function.compilerData.memSlotUpto
    return instructions
def makeBlockByteCode(block: Block, scopeInfo: ScopeInfo):
    instructions: list[Instruction] = []
    for i, statement in enumerate(block.statements):
        instructions.extend(makeStatementByteCode(statement, ScopeInfo(block, i)))
    return instructions


def reserveVariableMemorySlot(var_: Variable, scopeInfo: ScopeInfo) -> MemSlot:
    if isinstance(scopeInfo.scope, (FunctionDef, Block)):
        current = scopeInfo.scope
        while not isinstance(current, FunctionDef):
            assert isinstance(scopeInfo.scope, Block)
            current = current.parent_positioning.scope
        memSlotUpto = current.compilerData.memSlotUpto
        size = getTypeSize(var_.type_, scopeInfo)
        current.compilerData.memSlotUpto += size 
        return MemSlot(memSlotUpto, MemLocationKind.local_, size=size)
    raise
        

# @typechecked
def makeStatementByteCode(statement: Statement, scopeInfo: ScopeInfo, isFromConstructor=False) -> list[Instruction]:
    instructions: list[Instruction]|None
    match statement:
        case Variable(defaultValue=defaultValue):
            if not isFromConstructor:
                assert statement.compileTimeInfo_memSlot == None, f"this should be the first your making it"
            instructions: list[Instruction] = []
            mem_slot = reserveVariableMemorySlot(statement, scopeInfo)
            statement.compileTimeInfo_memSlot = mem_slot
            if defaultValue:
                instructions.extend(makeExpressionByteCode(defaultValue, scopeInfo))
                instructions.append(PlaceStackMemoryIntoSlot(mem_slot))
            return instructions
        case FunctionCall():
            return makeExpressionByteCode(statement, scopeInfo)
        case BuiltInFunction():
            return [statement]
        case ReturnStmt(expression):
            return makeExpressionByteCode(expression, scopeInfo)+[ReturnInstruction(getTypeSize(getExpressionType(expression, scopeInfo), scopeInfo))]
        case Block():
            return makeBlockByteCode(statement, scopeInfo)
        case IfStatement():
            instructions = makeExpressionByteCode(statement.expression, scopeInfo)
            thenBlockInstructions = makeBlockByteCode(statement.then, scopeInfo)
            instructions.append(JumpIfZero(len(thenBlockInstructions)))
            instructions.extend(thenBlockInstructions)
            return instructions

        case ClassReturn():
            return [ClassReturn()]
        case Assignment(left, right):
            instructions = makeExpressionByteCode(right, scopeInfo)
            size = getExpressionSize(right, scopeInfo)
            if isinstance(left, Deref):
                pointerType = getExpressionType(left.pointer, scopeInfo)
                assert pointerType.name == "pointer"
                instructions.extend(makeExpressionByteCode(left.pointer, scopeInfo))
                size = getTypeSize(pointerType.subtypes[0], scopeInfo)
                instructions.append(PlaceStackMemoryIntoMemslotOnStack(size))
            else:
                destinationSlot, _, _, addressInstructions = resolveMemoryLocation(left, scopeInfo)
                if destinationSlot is None:
                    assert isinstance(addressInstructions, list)
                    addressInstructions.append(PlaceStackMemoryIntoMemslotOnStack(size))
                    return instructions + addressInstructions
                instructions.append(PlaceStackMemoryIntoSlot(destinationSlot))
            return instructions
        case _:
            raise Exception(f"unhandled {statement}")


# @typechecked
def makeExpressionByteCode(expression: Expression, scopeInfo: ScopeInfo) -> list[Instruction]:
    match expression:
        case FunctionCall(functionReference, args):
            instructions: list[Instruction] = []
            for arg in args:
                instructions.extend(makeExpressionByteCode(arg, scopeInfo))
            functionDef, functionDefScopeInfo = resolveFunctionReferenceToDefinition(functionReference, scopeInfo)
            assert isinstance(functionDef, FunctionDef)
            if not functionDef.compilerData.functionRuntimeId:
                functionDef.compilerData.functionRuntimeId = runtime_data.functionIds
                runtime_data.functionIds+=1
            instructions.append(PushNumber(functionDef.compilerData.functionRuntimeId))
            instructions.append(CallFunctionWithParamStackSize(getTypeSize(getExpressionType(functionDef, functionDefScopeInfo), scopeInfo)))
            return instructions
        case Ident():
            memSlot, _, _, _ = resolveMemoryLocation(expression, scopeInfo)
            return [LoadMemoryFromSlot(memSlot)]
        case FieldAccess():
            memSlot, _, type_, instructions = resolveMemoryLocation(expression, scopeInfo)
            if memSlot == None:
                size = getTypeSize(type_, scopeInfo)
                instructions.append(DerefInstruction(size))
                return instructions
            return [LoadMemoryFromSlot(memSlot)]
        case Pointer():
            memSlot, scopeInfo, type_, instructions = resolveMemoryLocation(expression.pointsTo, scopeInfo)
            if memSlot == None:
                return instructions
            return [PlaceAbsoluteMemSlotOnStack(memSlot)]
        case Number(number):
            return [PushNumber(number)]
        case Deref():
            instructions = makeExpressionByteCode(expression.pointer, scopeInfo)
            type_ = getExpressionType(expression.pointer, scopeInfo)
            size = getTypeSize(type_.subtypes[0], scopeInfo)
            instructions.append(DerefInstruction(size))
            return instructions
        case Operation(op, left=left, right=right):
            return (
                makeExpressionByteCode(left, scopeInfo)
                + makeExpressionByteCode(right, scopeInfo)
                + [BinaryOperation(op)]
            )
        case _:
            raise TypeError(f"Unsupported expression: {expression!r}")







# @typechecked
def resolveMemoryLocation(expression: Expression, scopeInfo: ScopeInfo) -> tuple[MemSlot|None, ScopeInfo, Type, list[Instruction]|None]:
    """Return a static memory slot or instructions that push its runtime address."""
    match expression:
        case FieldAccess():
            objectsOffset, objectsScope, objectsType, _ = resolveMemoryLocation(expression.object, scopeInfo)
            if objectsType.name == "pointer":
                instructions = makeExpressionByteCode(expression.object, scopeInfo)
                cls,_  = getClass(objectsType.subtypes[0].subtypes[0].name, scopeInfo)
                field = cls.getFeild(expression.fieldName)
                instructions.append(OffsetPointer(
                    offset=field.compileTimeInfo_memSlot.memOffset,
                    size=field.compileTimeInfo_memSlot.size,
                ))
                return None, objectsScope, field.type_, instructions
            assert objectsType.name == "class"
            cls, clsScope = getClass(objectsType.subtypes[0].name, objectsScope)
            field = cls.getFeild(expression.fieldName)
            fieldsOffset = MemSlot(objectsOffset.memOffset+field.compileTimeInfo_memSlot.memOffset, 
                objectsOffset.memLocationKind, field.compileTimeInfo_memSlot.size
            )
            return fieldsOffset, objectsScope, field.type_, None
        case Ident():
            var_, varsScope = getVariable(expression, scopeInfo)
            assert isinstance(var_, Variable)
            assert var_.compileTimeInfo_memSlot, f"its {var_}"
            return var_.compileTimeInfo_memSlot, varsScope, var_.type_, None
        case _:
            raise
