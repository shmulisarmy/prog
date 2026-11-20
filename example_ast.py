from ast_ import Assignment, Block, FunctionCall, FunctionDef, Ident, IfStatement, Number, Operation, Program, ReturnStmt, ScopeInfo, Type, Variable
from builtInFunctions import BuiltInFunction
program = Program([
    Variable("void", Type("void")),
    Variable("main", Type("function", [Type("void")]), FunctionDef([], Type("void"), Block(
        [
            Variable("a", Type("int"), Number(8)),
            Variable("b", Type("int"), Operation("+", Number(29), Number(11))),
            Variable("c", Type("int"), Operation("+", Ident("a"), Ident("b"))),
            Variable("d", Type("int"), FunctionCall(Ident("add"), [Ident("a"), Ident("c")])),
            Block([
                Assignment(Ident("d"), Number(1)),
                IfStatement(Ident("d"), Block([
                    FunctionCall(Ident("printNumber"), [Ident("d")]),
                ]))
            ]),
            BuiltInFunction("printEntireStack"),
            FunctionCall(Ident("printNumber"), [FunctionCall(Ident("fib"), [Number(3)])]),
            FunctionCall(Ident("printNumber"), [FunctionCall(Ident("fib"), [Number(4)])]),
            FunctionCall(Ident("printNumber"), [FunctionCall(Ident("fib"), [Number(5)])]),
            FunctionCall(Ident("printNumber"), [FunctionCall(Ident("fib"), [Number(6)])]),
            FunctionCall(Ident("printNumber"), [FunctionCall(Ident("fib"), [Number(7)])]),
            FunctionCall(Ident("printNumber"), [FunctionCall(Ident("fib"), [Number(8)])]),
            FunctionCall(Ident("printNumber"), [FunctionCall(Ident("fib"), [Number(9)])]),
            FunctionCall(Ident("printNumber"), [FunctionCall(Ident("fib"), [Number(10)])]),
            FunctionCall(Ident("printNumber"), [Ident("a")]),
            FunctionCall(Ident("printNumber"), [Ident("a")]),
            FunctionCall(Ident("printNumber"), [Ident("a")]),
            FunctionCall(Ident("printNumber"), [Ident("a")]),
            FunctionCall(Ident("printNumber"), [Ident("a")]),
            BuiltInFunction("printEntireStack"),
            ReturnStmt(Ident("void"))
        ]
    ))),
    Variable("printNumber", Type("function", [Type("int")]), FunctionDef([Variable("a", Type("int"))], Type("void"), Block(
        [
            BuiltInFunction("printNumberOnStack"),
            ReturnStmt(Ident("void"))
        ]
    ))),
    Variable("add", Type("function", [Type("int"), Type("int"), Type("int")]), FunctionDef([Variable("a", Type("int")), Variable("b", Type("int"))], Type("int"), Block(
        [
            ReturnStmt(Operation("+", Ident("a"), Ident("b")))
        ]
    ))),
    Variable("fib", Type("function", [Type("int"), Type("int")]), FunctionDef([Variable("n", Type("int"))], Type("int"), Block(
        [
            IfStatement(Operation("<", Ident("n"), Number(3)), Block([
                ReturnStmt(Ident("n"))    
            ])),
            ReturnStmt(Operation("+", FunctionCall(Ident("fib"), [
                Operation("-", Ident("n"), Number(1)),
            ]),
            FunctionCall(Ident("fib"), [
                  Operation("-", Ident("n"), Number(2))
            ])
            ))
        ]
    )))
])