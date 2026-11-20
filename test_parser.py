import unittest
from pathlib import Path

from ast_ import (
    Assignment, Block, ClassDef, Deref, FieldAccess, FunctionCall, FunctionDef, Ident, IfStatement, Number,
    Operation, Pointer, Program, ReturnStmt, Type, Variable,
)
from parser import parse
from builtInFunctions import BuiltInFunction


class ParserTest(unittest.TestCase):
    def test_pointer_expression(self):
        expected = Variable("ap", Type("pointer", [Type("int")]), Pointer(pointsTo=Ident("a")))
        self.assertEqual(parse("ap pointer[int] = &a"), Program([expected]))
        program = parse("main := function() void { a int = 10; ap pointer[int] = &a }")
        self.assertEqual(program.symbols[0].defaultValue.body.statements[1], expected)

    def test_deref_expression(self):
        self.assertEqual(parse("a int = *ap"), Program([
            Variable("a", Type("int"), Deref(pointer=Ident("ap"))),
        ]))
        self.assertEqual(parse("a := *ap * 2"), Program([
            Variable("a", None, Operation("*", Deref(pointer=Ident("ap")), Number(2))),
        ]))

    def test_deref_assignment(self):
        program = parse("main := function() void { *ap = 100 }")
        self.assertEqual(program.symbols[0].defaultValue.body, Block([
            Assignment(Deref(pointer=Ident("ap")), Number(100)),
        ]))

    def test_class_declaration(self):
        source = "\n".join(Path(__file__).with_name("main.code").read_text().splitlines()[6:10])
        self.assertEqual(parse(source), Program([
            Variable("Person", Type("class"), ClassDef([
                Variable("id", Type("int")), Variable("age", Type("int"))])),
        ]))

    def test_class_values(self):
        fields = [Variable("id", Type("int"))]
        for declaration in ("Person :=", "Person class ="):
            with self.subTest(declaration=declaration):
                self.assertEqual(parse(declaration + " class { id int }"), Program([
                    Variable("Person", Type("class"), ClassDef(fields)),
                ]))
        program = parse("main := function() void { Person := class { id int }; Alias := Person }")
        self.assertEqual(program.symbols[0].defaultValue.body, Block([
            Variable("Person", Type("class"), ClassDef(fields)), Variable("Alias", None, Ident("Person")),
        ]))

    def test_main_code(self):
        source = Path(__file__).with_name("main.code").read_text()
        program = parse(source, "main.code")
        self.assertEqual(program.symbols[2], Variable("add", Type("function", [Type("int"), Type("int")]), FunctionDef(
            [Variable("a", Type("int")), Variable("b", Type("int"))],
            Type("int"), Block([ReturnStmt(Operation("+", Ident("a"), Ident("b")))]))))
        self.assertEqual([symbol.name for symbol in program.symbols], ["void", "Person", "add", "fib", "main"])
        self.assertEqual(program.symbols[4].defaultValue.body.statements[2],
                         Variable("n", Type("int"), Operation("+",
                             FieldAccess(Ident("person"), "age"), FieldAccess(Ident("person"), "age"))))
        self.assertEqual(program.symbols[4].defaultValue.body.statements[3],
                         Assignment(FieldAccess(Ident("person"), "age"), Number(1)))
        self.assertEqual(program.symbols[4].defaultValue.body.statements[6],
                         BuiltInFunction("printEntireStack"))

    def test_field_assignment(self):
        program = parse("main := function() void { person.age=1; person.parent.age = person.age + 1 }")
        self.assertEqual(program.symbols[0].defaultValue.body, Block([
            Assignment(FieldAccess(Ident("person"), "age"), Number(1)),
            Assignment(FieldAccess(FieldAccess(Ident("person"), "parent"), "age"),
                       Operation("+", FieldAccess(Ident("person"), "age"), Number(1))),
        ]))

    def test_field_access(self):
        self.assertEqual(parse("n int = person.age + 1"), Program([
            Variable("n", Type("int"), Operation("+", FieldAccess(Ident("person"), "age"), Number(1))),
        ]))
        self.assertEqual(parse("n := getPerson().parent.age"), Program([
            Variable("n", None, FieldAccess(FieldAccess(FunctionCall(Ident("getPerson"), []), "parent"), "age")),
        ]))
        self.assertEqual(parse("n := person.getAge()"), Program([
            Variable("n", None, FunctionCall(FieldAccess(Ident("person"), "getAge"), [])),
        ]))
        for source in ("n := person.", "n := person.123", "n := person..age"):
            with self.subTest(source=source), self.assertRaises(SyntaxError):
                parse(source)

    def test_builtin_statement(self):
        program = parse("main := function() void { :printEntireStack; :printNumberOnStack }")
        self.assertEqual(program.symbols[0].defaultValue.body, Block([
            BuiltInFunction("printEntireStack"), BuiltInFunction("printNumberOnStack"),
        ]))
        for statement in (":", ":123", ":printEntireStack()"):
            with self.subTest(statement=statement), self.assertRaises(SyntaxError):
                parse("main := function() void { " + statement + " }")

    def test_untyped_declarations(self):
        self.assertEqual(parse("x := 1 + 2"), Program([
            Variable("x", None, Operation("+", Number(1), Number(2)))]))
        program = parse("main := function() void { x := 1; y int = 2; x = y }")
        self.assertIsNone(program.symbols[0].type_)
        self.assertEqual(program.symbols[0].defaultValue.body, Block([
            Variable("x", None, Number(1)), Variable("y", Type("int"), Number(2)),
            Assignment(Ident("x"), Ident("y")),
        ]))

    def test_recursive_function(self):
        program = parse('''fib function[int, int] = function(n int) int {
            if (n < 3) { return n }
            return fib(n - 1) + fib(n - 2)
        }''')
        self.assertEqual(program.symbols[0].defaultValue, FunctionDef(
            [Variable("n", Type("int"))], Type("int"), Block([
                IfStatement(Operation("<", Ident("n"), Number(3)), Block([ReturnStmt(Ident("n"))])),
                ReturnStmt(Operation("+",
                    FunctionCall(Ident("fib"), [Operation("-", Ident("n"), Number(1))]),
                    FunctionCall(Ident("fib"), [Operation("-", Ident("n"), Number(2))]))),
            ])))

    def test_precedence_calls_and_blocks(self):
        program = parse('''main function[void] = function() void {
            a int = 20 - 6 - 2 * 3
            { a = (20 - 6) // 2 % 3 }
            printNumber(add(
                a, -2,
            ))
            if (a > 0) { return void }
            else { return void }
        }''')
        statements = program.symbols[0].defaultValue.body.statements
        self.assertEqual(statements[0].defaultValue, Operation("-",
            Operation("-", Number(20), Number(6)), Operation("*", Number(2), Number(3))))
        self.assertIsInstance(statements[1], Block)
        self.assertEqual(statements[2], FunctionCall(Ident("printNumber"), [
            FunctionCall(Ident("add"), [Ident("a"), Operation("-", Number(0), Number(2))])]))
        self.assertEqual(statements[3].else_, Block([ReturnStmt(Ident("void"))]))

    def test_invalid_syntax(self):
        for source in ["x :=", "x : = 1", "x int := 1", "x int =", "x int @", "x int y int", "x function[void] = function() void {",
                       "class Person {}", "Person := class {", "Person := class { id int age int }",
                       "x int = f(1 2)", "x int = 1 + / 2",
                       "x function[void] = function() void { f() = 2 }"]:
            with self.subTest(source=source), self.assertRaises(SyntaxError):
                parse(source)
        with self.assertRaises(SyntaxError) as error:
            parse("x int\ny int = @", "bad.code")
        self.assertEqual((error.exception.lineno, error.exception.offset), (2, 9))


if __name__ == "__main__":
    unittest.main()
