import unittest

from ast_ import ScopeInfo
from generate_bytecode import makeExpressionByteCode
from instructions import BinaryOperation, PushNumber
from parser import parse
from source_range import Position, Range
from vm import Vm


position = Position('test.code', 1, 1)
DEBUG_LOCATION = dict(range=Range(position, position), created_at=__file__)


def compile_expression(source):
    program = parse('value := ' + source, 'test.code')
    return makeExpressionByteCode(program.symbols[0].defaultValue, ScopeInfo(program))


class VMTest(unittest.TestCase):
    def test_literal_and_independent_stacks(self):
        vm = Vm(compile_expression('8'))
        vm.execute()
        self.assertEqual(vm.stack, [8])
        empty = Vm([])
        empty.execute()
        self.assertEqual(empty.stack, [])
        self.assertEqual(vm.stack, [8])

    def test_nested_expression(self):
        instructions = compile_expression('20 - 3 * 4')
        self.assertEqual(instructions, [
            PushNumber(20, **DEBUG_LOCATION), PushNumber(3, **DEBUG_LOCATION),
            PushNumber(4, **DEBUG_LOCATION), BinaryOperation('*', **DEBUG_LOCATION),
            BinaryOperation('-', **DEBUG_LOCATION),
        ])
        vm = Vm(instructions)
        vm.execute()
        self.assertEqual(vm.stack, [8])

    def test_arithmetic(self):
        for op, expected in [('+', 10), ('-', 4), ('*', 21), ('/', 7 / 3), ('//', 2), ('%', 1)]:
            with self.subTest(op=op):
                vm = Vm(compile_expression('7 ' + op + ' 3'))
                vm.execute()
                self.assertEqual(vm.stack, [expected])

    def test_invalid_input(self):
        with self.assertRaises(NameError):
            compile_expression('missing')
        with self.assertRaises(ValueError):
            Vm([BinaryOperation('+', **DEBUG_LOCATION)]).execute()
        with self.assertRaises(ValueError):
            Vm([PushNumber(1, **DEBUG_LOCATION), PushNumber(2, **DEBUG_LOCATION),
                BinaryOperation('unknown', **DEBUG_LOCATION)]).execute()
        with self.assertRaises(ZeroDivisionError):
            Vm(compile_expression('1 / 0')).execute()


if __name__ == '__main__':
    unittest.main()
