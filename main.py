from typeguard import typechecked
from ast_ import Block, ClassDef, FunctionCall, FunctionDef, Ident, IfStatement, Number, Operation, Program, ReturnStmt, ScopeInfo, Type, Variable
from compilerTools import getTypeSize, getVariable
from generate_bytecode import makeFunctionByteCode
from instructions import CallFunctionWithParamStackSize, PushNumber
from more_compiler_tools import assignFieldOffsets
from parser import parse_file
import runtime_data
from runtime_data_types import MemLocationKind, MemSlot
from typeChecker import typeCheckFunction
from vm import Vm


program = parse_file("main.code")




def setUpParentPositioningWithinBlock(block: Block):
    for (i, statement) in enumerate(block.statements):
        if isinstance(statement, Block):
            statement.parent_positioning = ScopeInfo(block, i)
            setUpParentPositioningWithinBlock(statement)
        if isinstance(statement, IfStatement):
            statement.then.parent_positioning = ScopeInfo(block, i)
            setUpParentPositioningWithinBlock(statement.then)
            if statement.else_:
                statement.else_.parent_positioning = ScopeInfo(block, i)
                setUpParentPositioningWithinBlock(statement.else_)

@typechecked
def setUpParentPositioningWithinFunction(function: FunctionDef):
    function.body.parent_positioning = ScopeInfo(function)
    setUpParentPositioningWithinBlock(function.body)

for symbol in program.symbols:
    if isinstance(symbol.defaultValue, FunctionDef):
        continue
    if isinstance(symbol.defaultValue, ClassDef):
        continue
    size = getTypeSize(symbol.type_, ScopeInfo(program))
    symbol.compileTimeInfo_memSlot = MemSlot(runtime_data.globalMemBumSlot, MemLocationKind.global_, size)
    runtime_data.globalMemBumSlot+=size
    

    
for symbol in program.symbols:
    if isinstance(symbol.defaultValue, ClassDef):
        symbol.defaultValue.parent_positioning = ScopeInfo(program)




for symbol in program.symbols:
    if not isinstance(symbol.defaultValue, ClassDef):
        continue
    assignFieldOffsets(symbol.defaultValue)
        
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










vm = Vm(runtime_data.functionInstructions)
vm.stack.extend([None] * runtime_data.globalMemBumSlot)
vm.instructions.append(PushNumber(main_function.compilerData.functionRuntimeId))
vm.instructions.append(CallFunctionWithParamStackSize(0))
vm.execute()





getTypeSize(program.symbols[0].type_, ScopeInfo(Program, 0))
