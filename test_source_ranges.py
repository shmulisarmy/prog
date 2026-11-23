import inspect
import unittest
from dataclasses import fields
from pathlib import Path
from typing import get_args

from builtInFunctions import BuiltInFunction
from current_line import current_line
from generate_bytecode import makeExpressionByteCode, makeStatementByteCode
from instructions import Instruction, PushNumber
from ast_ import ScopeInfo
from parser import parse, parse_file
from source_range import Node, Position, Range


class SourceRangeTest(unittest.TestCase):
    def check_tree(self, node, source, filename):
        if isinstance(node, list):
            for child in node:
                self.check_tree(child, source, filename)
        elif isinstance(node, (Node, BuiltInFunction)):
            self.assertIsInstance(node.range, Range, type(node).__name__)
            offsets = []
            lines = source.splitlines(keepends=True) + ['']
            for position in (node.range.start, node.range.end):
                self.assertEqual(position.filename, filename)
                self.assertGreaterEqual(position.line, 1)
                self.assertGreaterEqual(position.character, 1)
                offset = sum(map(len, lines[:position.line - 1])) + position.character - 1
                self.assertLessEqual(offset, len(source))
                offsets.append(offset)
            self.assertLessEqual(*offsets)
            for f in fields(node):
                if f.name != 'range':
                    child = getattr(node, f.name)
                    if isinstance(child, (Node, BuiltInFunction)):
                        self.assertGreaterEqual(child.range.start.line, node.range.start.line)
                        self.assertLessEqual(child.range.end.line, node.range.end.line)
                    self.check_tree(child, source, filename)

    def test_exact_ranges(self):
        source = '# comment\nx := foo(12).age + -3  # trailing\n'
        program = parse(source, 'example.code')
        variable = program.symbols[0]
        operation = variable.defaultValue
        field = operation.left
        call = field.object
        negative = operation.right
        for node, start, end in [
            (variable, 1, 22), (operation, 6, 22), (field, 6, 17),
            (call, 6, 13), (call.functionReference, 6, 9),
            (call.args[0], 10, 12), (negative, 20, 22),
            (negative.left, 20, 21), (negative.right, 21, 22),
        ]:
            self.assertEqual(node.range, Range(Position('example.code', 2, start),
                                               Position('example.code', 2, end)))
        self.assertEqual(program.range, Range(Position('example.code', 1, 1),
                                              Position('example.code', 3, 1)))
        self.check_tree(program, source, 'example.code')

    def test_every_parsed_node_has_range(self):
        source = '''Person := class { id int; age int }
main := function(a pointer[int], b int) void {
    p := new (1 + 2)
    ap := &a
    *ap = +b
    person.age = f(a, -2)
    { :printEntireStack }
    if (b > 0) { return b }
    else { return *ap }
}
'''
        self.check_tree(parse(source, 'all.code'), source, 'all.code')
        filename = str(Path(__file__).with_name('main.code'))
        self.check_tree(parse_file(filename), Path(filename).read_text(), filename)
        self.check_tree(parse('', 'empty.code'), '', 'empty.code')

    def test_instructions_require_debug_locations(self):
        for instruction in get_args(Instruction):
            for name in ('range', 'created_at'):
                with self.subTest(instruction=instruction.__name__, field=name):
                    parameter = inspect.signature(instruction).parameters[name]
                    self.assertEqual(parameter.default, inspect.Parameter.empty)
                    self.assertEqual(parameter.kind, inspect.Parameter.KEYWORD_ONLY)
        with self.assertRaisesRegex(TypeError, "'range' and 'created_at'"):
            PushNumber(1)
        position = Position('test.code', 1, 1)
        with self.assertRaisesRegex(TypeError, "'created_at'"):
            PushNumber(1, range=Range(position, position))

    def test_created_at_is_instruction_creation_site(self):
        source = 'main := function() void { x := 1 + 2; :printEntireStack }'
        program = parse(source, 'test.code')
        variable, builtin = program.symbols[0].defaultValue.body.statements
        instructions = makeExpressionByteCode(variable.defaultValue, ScopeInfo(program))
        instructions += makeStatementByteCode(builtin, ScopeInfo(program))
        self.assertEqual(len(instructions), 4)
        self.assertIsNot(instructions[-1], builtin)
        self.assertEqual(instructions[-1].range, builtin.range)
        for instruction in instructions:
            filename, line = instruction.created_at.rsplit(':', 1)
            self.assertEqual(Path(filename).name, 'generate_bytecode.py')
            self.assertIn(type(instruction).__name__ + '(',
                          Path(filename).read_text().splitlines()[int(line) - 1])
        self.assertNotEqual(instructions[0].created_at, instructions[2].created_at)

    def test_current_line_reports_direct_caller(self):
        expected = inspect.currentframe().f_lineno + 1
        self.assertEqual(current_line(), f"{__file__}:{expected}")


if __name__ == '__main__':
    unittest.main()
