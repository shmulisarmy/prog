from current_line import current_line

from sizeOf import SizeOf
from typing import TypeAlias

from ast_ import Assignment, Block, ClassDef, ClassReturn, Deref, Expression, FieldAccess, FunctionCall, FunctionDef, Ident, IfStatement, New, Number, Operation, Pointer, Program, ReturnStmt, ScopeInfo, Statement, Type, Variable
from builtInFunctions import BuiltInFunction
from compilerTools import getClass, getExpressionType, getTypeSize, getVariable, resolveFunctionReferenceToDefinition
from instructions import Allocate, OffsetPointer, BinaryOperation, CallFunctionWithParamStackSize, DerefInstruction, Instruction, JumpIfZero, PlaceAbsoluteMemSlotOnStack, PlaceStackMemoryIntoMemslotOnStack, PlaceStackMemoryIntoSlot, PushNumber, ReturnInstruction, OffsetOfField
import runtime_data
from runtime_data_types import MemLocationKind, MemSlot


varName: TypeAlias = str
Size: TypeAlias = int
def makeFunctionByteCode(function: FunctionDef, scopeInfo: ScopeInfo, isFromConstructor = False) -> list[Instruction]:
    instructions: list[Instruction] = []
    for param in function.params:
        instructions.extend(makeStatementByteCode(param, ScopeInfo(function), isFromConstructor=isFromConstructor))
    instructions.extend(makeBlockByteCode(function.body, ScopeInfo(function, 0)))
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
    if isinstance(scopeInfo.scope, (Program)):
        size = getTypeSize(var_.type_, scopeInfo)
        memSlot = MemSlot(runtime_data.globalMemBumpSlot, MemLocationKind.global_, size)
        runtime_data.globalMemBumpSlot+=size
        return memSlot
    raise


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
                instructions.append(PlaceStackMemoryIntoSlot(mem_slot, range=statement.range, created_at=current_line()))
            return instructions
        case FunctionCall():
            return makeExpressionByteCode(statement, scopeInfo)
        case BuiltInFunction():
            return [BuiltInFunction(statement.name, range=statement.range, created_at=current_line())]
        case ReturnStmt(expression):
            return makeExpressionByteCode(expression, scopeInfo)+[ReturnInstruction(SizeOf(getExpressionType(expression, scopeInfo)), range=expression.range, created_at=current_line())]
        case Block():
            return makeBlockByteCode(statement, scopeInfo)
        case IfStatement():
            instructions = makeExpressionByteCode(statement.expression, scopeInfo)
            thenBlockInstructions = makeBlockByteCode(statement.then, scopeInfo)
            instructions.append(JumpIfZero(len(thenBlockInstructions), range=statement.range, created_at=current_line()))
            instructions.extend(thenBlockInstructions)
            return instructions
        case ClassReturn():
            return [ClassReturn(range=statement.range, created_at=current_line())]
        case Assignment(left, right):
            instructions = makeExpressionByteCode(right, scopeInfo)
            expressionType = getExpressionType(right, scopeInfo)
            if isinstance(left, Deref):
                pointerType = getExpressionType(left.pointer, scopeInfo)
                assert pointerType.name == "pointer"
                instructions.extend(makeExpressionByteCode(left.pointer, scopeInfo))
                instructions.append(PlaceStackMemoryIntoMemslotOnStack(SizeOf(pointerType.subtypes[0]), range=statement.range, created_at=current_line()))
            else:
                instructions.extend(makeExpressionByteCode(left, scopeInfo))
                assert isinstance(instructions[-1], DerefInstruction), f"its {instructions[-1]}"
                instructions.pop()
                instructions.append(PlaceStackMemoryIntoMemslotOnStack(SizeOf(expressionType), range=statement.range, created_at=current_line()))
            return instructions
        case _:
            raise Exception(f"unhandled {statement}")


def putUnderDeref(instructions: list[Instruction], instruction: Instruction):
    p = instructions.pop()
    assert isinstance(p, DerefInstruction), f"its {p}"
    instructions.append(instruction)
    instructions.append(p)

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
            instructions.append(PushNumber(functionDef.compilerData.functionRuntimeId, range=expression.functionReference.range, created_at=current_line()))
            instructions.append(CallFunctionWithParamStackSize(SizeOf(getExpressionType(functionDef, functionDefScopeInfo)), range=expression.range, created_at=current_line()))
            return instructions
        case Ident():
            var_, varsScope = getVariable(expression, scopeInfo)
            assert isinstance(var_, Variable)
            assert var_.compileTimeInfo_memSlot, f"its {var_}"
            return [PlaceAbsoluteMemSlotOnStack(var_.compileTimeInfo_memSlot, range=expression.range, created_at=current_line()), DerefInstruction(SizeOf(var_.type_), range=expression.range, created_at=current_line())]
        case FieldAccess():
            _, objectsScope = getVariable(expression.object, scopeInfo)
            objectsType = getExpressionType(expression.object, scopeInfo)
            if objectsType.name == "pointer":
                instructions = makeExpressionByteCode(expression.object, scopeInfo)
                cls,_  = getClass(objectsType.subtypes[0].subtypes[0].name, scopeInfo)
                field = cls.getField(expression.fieldName)
                instructions.append(OffsetPointer(
                    offset=OffsetOfField(cls, expression.fieldName),
                    newSize=SizeOf(field.type_),
                    range=expression.range, created_at=current_line()
                ))
                instructions.append(DerefInstruction(
                    SizeOf(field.type_),
                    range=expression.range, created_at=current_line()
                ))
                return instructions
            assert objectsType.name == "class"
            instructions = makeExpressionByteCode(expression.object, scopeInfo)
            cls, clsScope = getClass(objectsType.subtypes[0].name, objectsScope)
            field = cls.getField(expression.fieldName)
            putUnderDeref(instructions, OffsetPointer(
                offset=OffsetOfField(cls, expression.fieldName),
                newSize=SizeOf(field.type_),
                range=expression.range, created_at=current_line()
            ))
            instructions[-1].size = SizeOf(field.type_)
            return instructions
        case Pointer():
            instructions = makeExpressionByteCode(expression.pointsTo, scopeInfo)
            assert isinstance(instructions[-1], DerefInstruction)
            instructions.pop()
            return instructions
        case Number(number):
            return [PushNumber(number, range=expression.range, created_at=current_line())]
        case Deref():
            instructions = makeExpressionByteCode(expression.pointer, scopeInfo)
            type_ = getExpressionType(expression.pointer, scopeInfo)
            size = getTypeSize(type_.subtypes[0], scopeInfo)
            instructions.append(DerefInstruction(SizeOf(type_), range=expression.range, created_at=current_line()))
            return instructions
        case New():
            instructions = makeExpressionByteCode(expression.expression, scopeInfo)
            type_ = getExpressionType(expression.expression, scopeInfo)
            instructions.append(Allocate(SizeOf(type_), range=expression.range, created_at=current_line()))
            instructions.append(PlaceStackMemoryIntoMemslotOnStack(SizeOf(type_), keepSlotAround=True, range=expression.range, created_at=current_line()))
            return instructions
        case Operation(op, left=left, right=right):
            return (
                makeExpressionByteCode(left, scopeInfo)
                + makeExpressionByteCode(right, scopeInfo)
                + [BinaryOperation(op, range=expression.range, created_at=current_line())]
            )
        case _:
            raise TypeError(f"Unsupported expression: {expression!r}")
