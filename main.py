from current_line import current_line
from sizeOf import SizeOf
from dataclasses import fields
from parent_referencing import setUpParentPositioningWithinFunction
from ast_ import ClassDef, FunctionDef, Ident, ScopeInfo
from compilerTools import getTypeSize, getVariable
from generate_bytecode import makeFunctionByteCode, makeStatementByteCode
from instructions import CallFunctionWithParamStackSize, Instruction, PushNumber, OffsetOfField
from more_compiler_tools import assignFieldOffsets
from parser import parse_file
import runtime_data
from source_range import Position, Range
from typeChecker import typeCheckFunction, typeCheckVariable
from vm import Vm


program = parse_file("main.code")


for symbol in program.symbols:
    if not isinstance(symbol.defaultValue, ClassDef):
        continue
    symbol.defaultValue.parent_positioning = ScopeInfo(program)
    assignFieldOffsets(symbol.defaultValue)


global_instructions: list[Instruction] = []
for symbol in program.symbols:
    if isinstance(symbol.defaultValue, FunctionDef):
        continue
    if isinstance(symbol.defaultValue, ClassDef):
        continue
    typeCheckVariable(symbol, ScopeInfo(program))
    global_instructions.extend(makeStatementByteCode(symbol, ScopeInfo(program)))


for symbol in program.symbols:
    if not isinstance(symbol.defaultValue, FunctionDef):
        continue
    function = symbol.defaultValue
    function.parent_positioning = ScopeInfo(program)
    setUpParentPositioningWithinFunction(function)
    typeCheckFunction(function)
    assert isinstance(function, FunctionDef)
    if not function.compilerData.functionRuntimeId:
        function.compilerData.functionRuntimeId = runtime_data.functionIds
        runtime_data.functionIds+=1
    runtime_data.FunctionInstructionStartLocations[function.compilerData.functionRuntimeId] = len(runtime_data.functionInstructions)
    runtime_data.functionInstructions.extend(makeFunctionByteCode(function, ScopeInfo(program), isFromConstructor=function.isConstructor))

for function in runtime_data.FunctionDefinitionsToTurnIntoInstructions:
    function.parent_positioning = ScopeInfo(program)
    setUpParentPositioningWithinFunction(function)
    typeCheckFunction(function)
    assert isinstance(function, FunctionDef)
    if not function.compilerData.functionRuntimeId:
        function.compilerData.functionRuntimeId = runtime_data.functionIds
        runtime_data.functionIds+=1
    runtime_data.FunctionInstructionStartLocations[function.compilerData.functionRuntimeId] = len(runtime_data.functionInstructions)
    runtime_data.functionInstructions.extend(makeFunctionByteCode(function, ScopeInfo(program), isFromConstructor=function.isConstructor))


main_function_symbol, _ = getVariable(Ident("main"), ScopeInfo(program))
main_function = main_function_symbol.defaultValue
assert isinstance(main_function, FunctionDef)


all_instructions = runtime_data.functionInstructions+global_instructions

for instruction in all_instructions:
    for f in fields(instruction):
        if isinstance(getattr(instruction, f.name), SizeOf):
            so: SizeOf = getattr(instruction, f.name)
            setattr(instruction, f.name, getTypeSize(so.type_, ScopeInfo(program)))
        if isinstance(getattr(instruction, f.name), OffsetOfField):
            so: OffsetOfField = getattr(instruction, f.name)
            field = so.cls.getField(so.field)
            setattr(instruction, f.name, field.compileTimeInfo_memSlot.memOffset)


start_ = Range(start=Position("start_.code", 0, 0), end=Position("start_.code", 0, 0))
vm = Vm(all_instructions)
vm.instructions.append(PushNumber(main_function.compilerData.functionRuntimeId, range=start_, created_at=current_line()))
vm.instructions.append(CallFunctionWithParamStackSize(0, range=start_, created_at=current_line()))
vm.stack.extend([None] * runtime_data.globalMemBumpSlot)
vm.instructionPtr = len(runtime_data.functionInstructions)
vm.execute()
