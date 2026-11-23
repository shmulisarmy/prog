from typeguard import typechecked
from ast_ import ScopeInfo, FunctionDef, Block, IfStatement
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
