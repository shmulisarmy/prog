from typeguard import typechecked as typecheck

from ast_ import Assignment, Block, Expression, FunctionCall, FunctionDef, ScopeInfo, Type, Variable
from compilerTools import getExpressionType, iterReturnStmts, resolveFunctionReferenceToDefinition
import utils


@typecheck
def typeCheckExpression(expression: Expression, scopeInfo: ScopeInfo):
    match expression:
        case FunctionCall():
            (func, _) = resolveFunctionReferenceToDefinition(expression.functionReference, scopeInfo)
            functionType = getExpressionType(func, func.parent_positioning)
            assert isinstance(functionType, Type), (
                f"Function {expression.functionReference!r}: expected a function type, "
                f"got {functionType!r}"
            )
            functionName = utils.cyan(expression.functionReference.name)
            assert len(func.params) == len(expression.args), (
                f"Function {functionName}: expected {utils.green(len(func.params))} arguments, "
                f"got {utils.red(len(expression.args))}; "
                f"parameters: {', '.join(f'{p.name}: {p.type_}' for p in func.params) or '(none)'}"
            )
            for i, (arg, param) in enumerate(zip(expression.args, func.params), start=1):
                actual_type = getExpressionType(arg, scopeInfo)
                assert param.type_ == actual_type, (
                    f"Function {functionName}, argument {i} ({utils.cyan(param.name)}): "
                    f"expected {param.type_}, got {actual_type} for value {arg!r}"
                )


@typecheck
def typeCheckVariable(variable: Variable, scopeInfo: ScopeInfo):
    if not variable.defaultValue:
        return
    actual_type = getExpressionType(variable.defaultValue, scopeInfo)
    assert actual_type == variable.type_, (
        f"Variable {variable.name!r}: expected {utils.green(variable.type_)}, "
        f"got {utils.green(actual_type)} for value {variable.defaultValue!r}"
    )
    typeCheckExpression(variable.defaultValue, scopeInfo)


@typecheck
def typeCheckFunction(function: FunctionDef):
    for param in function.params:
        typeCheckVariable(param, ScopeInfo(function, None))
    typeCheckBlock(function.body)
    for (stmt, scopeInfo) in iterReturnStmts(function.body):
        actual_type = getExpressionType(stmt.value, scopeInfo)
        assert actual_type == function.ReturnType, (
            f"Return type mismatch: expected {utils.green(function.ReturnType)}, "
            f"got {utils.green(actual_type)} for expression {stmt.value!r}"
        )



@typecheck    
def typeCheckBlock(block: Block):
    for i, stmt in enumerate(block.statements):
        match stmt:
            case Assignment(right=right):
                typeCheckExpression(right, ScopeInfo(block, i))
            case FunctionCall():
                typeCheckExpression(stmt, ScopeInfo(block, i))
            case Variable():
                typeCheckVariable(stmt, ScopeInfo(block, i))
            case Block():
                typeCheckBlock(stmt)
