import re
import unittest

from ast_ import (
    Block, FunctionCall, FunctionDef, Ident, Number, Operation, Program,
    ReturnStmt, ScopeInfo, String, Type, Variable,
)
from compilerTools import getExpressionType, getTypeSize
from typeChecker import typeCheckExpression, typeCheckFunction, typeCheckVariable


class TypeCheckerDiagnosticsTest(unittest.TestCase):
    def test_diagnostics(self):
        integer, string = Type("int"), Type("string")
        function = FunctionDef([Variable("a", integer), Variable("b", integer)],
                               integer, Block([ReturnStmt(Number(1))]))
        scope = ScopeInfo(Program([
            Variable("add", Type("function", [integer, integer, integer]), function),
            Variable("value", integer, Number(1)),
        ]))
        function.parent_positioning = scope
        cases = [
            (lambda: typeCheckExpression(FunctionCall(Ident("add"), [Number(1)] * 4), scope),
             "Function add: expected 2 arguments, got 4; parameters: a: int, b: int"),
            (lambda: typeCheckExpression(FunctionCall(Ident("add"), [Number(1), String("x")]), scope),
             "Function add, argument 2 (b): expected int, got string"),
            (lambda: typeCheckVariable(Variable("x", integer, String("x")), scope),
             "Variable 'x': expected int, got string"),
            (lambda: typeCheckFunction(FunctionDef([], integer, Block([ReturnStmt(String("x"))]))),
             "Return type mismatch: expected int, got string"),
            (lambda: getExpressionType(Operation("+", Number(1), String("x")), scope),
             "Operator + requires matching operand types: left is int, right is string"),
            (lambda: typeCheckExpression(FunctionCall(Ident("missing"), []), scope),
             "Unknown variable missing"),
            (lambda: typeCheckExpression(FunctionCall(Ident("value"), []), scope),
             "Cannot call value: expected a function, got variable of type int"),
            (lambda: getTypeSize(Type("string"), scope),
             "Cannot determine storage size for type string"),
        ]
        for check, expected in cases:
            with self.subTest(expected=expected):
                with self.assertRaises((AssertionError, NameError, TypeError)) as error:
                    check()
                message = str(error.exception)
                self.assertIn(expected, re.sub(r"\x1b\[[0-9;]*m", "", message))
                self.assertIn("\x1b[", message)

        typeCheckExpression(FunctionCall(Ident("add"), [Number(1), Number(2)]), scope)
        signature = str(Type("function", [integer, Type("function", [string, integer])]))
        self.assertEqual(re.sub(r"\x1b\[[0-9;]*m", "", signature),
                         "function[int, function[string, int]]")


if __name__ == "__main__":
    unittest.main()
