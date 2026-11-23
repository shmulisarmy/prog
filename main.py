from current_line import current_line
from sizeOf import SizeOf
from dataclasses import fields
from parent_referencing import setUpParentPositioningWithinFunction
from ast_ import ClassDef, FunctionDef, Ident, ScopeInfo
from compilerTools import getTypeSize, getVariable
from generate_bytecode import makeFunctionByteCode, makeStatementByteCode
from instructions import CallFunctionWithParamStackSize, Instruction, PushFunctionDefReference, PushNumber, OffsetOfField
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
    if not symbol.defaultValue.compilerData.irInstructions:
        symbol.defaultValue.compilerData.irInstructions = makeFunctionByteCode(function, ScopeInfo(program), isFromConstructor=function.isConstructor)

for function in runtime_data.FunctionDefinitionsToTurnIntoInstructions:
    function.parent_positioning = ScopeInfo(program)
    setUpParentPositioningWithinFunction(function)
    typeCheckFunction(function)
    assert isinstance(function, FunctionDef)
    if not function.compilerData.irInstructions:
        function.compilerData.irInstructions = makeFunctionByteCode(function, ScopeInfo(program), isFromConstructor=function.isConstructor)
    


for function in runtime_data.FunctionDefinitionsToTurnIntoInstructions:
    for instanciation, _ in function.instanciations.items():
        assert len(instanciation) == len(function.genericParams) 
        type_map = {}
        for genericArg, genericParam in zip(instanciation, function.genericParams):
            type_map[genericParam] = genericArg
        function.type_map = type_map

        if function.instanciations[instanciation] == None:
            function.instanciations[instanciation] = runtime_data.functionIds
            runtime_data.functionIds+=1
        runtime_data.FunctionInstructionStartLocations[function.instanciations[instanciation]] = len(runtime_data.functionInstructions)


        for instruction in enumerate(function.compilerData.irInstructions):
            for f in fields(instruction):
                if isinstance(getattr(instruction, f.name), SizeOf):
                    so: SizeOf = getattr(instruction, f.name)
                    setattr(instruction, f.name, getTypeSize(so.type_, ScopeInfo(program)))
                if isinstance(getattr(instruction, f.name), OffsetOfField):
                    so: OffsetOfField = getattr(instruction, f.name)
                    field = so.cls.getField(so.field)
                    setattr(instruction, f.name, field.compileTimeInfo_memSlot.memOffset)
            if isinstance(instruction, PushFunctionDefReference):
                instruction = PushNumber(instruction.function.compilerData.functionRuntimeId, range=instruction.range, created_at=instruction.created_at)
            
            runtime_data.functionInstructions.append(instruction)
        raise
        runtime_data.FunctionStackBumpSize[function.compilerData.functionRuntimeId] = function.compilerData.memSlotUpto
        




for instructionIndex, instruction in enumerate(runtime_data.functionInstructions):
    if isinstance(instruction, PushFunctionDefReference):
        functionId = instruction.function.instanciations[instanciation]
        runtime_data.functionInstructions[instructionIndex] = PushNumber(functionId, range=instruction.range, created_at=instruction.created_at)




        


main_function_symbol, _ = getVariable(Ident("main"), ScopeInfo(program))
main_function = main_function_symbol.defaultValue
assert isinstance(main_function, FunctionDef)


all_instructions = runtime_data.functionInstructions+global_instructions



start_ = Range(start=Position("start_.code", 0, 0), end=Position("start_.code", 0, 0))
vm = Vm(all_instructions)
vm.instructions.append(PushNumber(main_function.compilerData.functionRuntimeId, range=start_, created_at=current_line()))
vm.instructions.append(CallFunctionWithParamStackSize(0, range=start_, created_at=current_line()))
vm.stack.extend([None] * runtime_data.globalMemBumpSlot)
vm.instructionPtr = len(runtime_data.functionInstructions)
vm.execute()
