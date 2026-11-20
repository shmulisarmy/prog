import unittest

from ast_ import Ident, Number, Operation
from instructions import BinaryOperation, PushNumber
from main import makeExpressionByteCode
from vm import Vm


class VMTest(unittest.TestCase):
    def setUp(self):
        self.vm = Vm()

    def test_literal_and_fresh_stack(self):
        self.assertEqual(self.vm.execute(makeExpressionByteCode(Number(8))), [8])
        self.assertEqual(self.vm.execute([]), [])

    def test_nested_expression(self):
        expression = Operation("-", Number(20), Operation("*", Number(3), Number(4)))
        self.assertEqual(makeExpressionByteCode(expression), [
            PushNumber(20), PushNumber(3), PushNumber(4),
            BinaryOperation("*"), BinaryOperation("-"),
        ])
        self.assertEqual(self.vm.execute(makeExpressionByteCode(expression)), [8])

    def test_arithmetic(self):
        for op, expected in [("+", 10), ("-", 4), ("*", 21), ("/", 7 / 3), ("//", 2), ("%", 1)]:
            with self.subTest(op=op):
                expression = Operation(op, Number(7), Number(3))
                self.assertEqual(self.vm.execute(makeExpressionByteCode(expression)), [expected])

    def test_invalid_input(self):
        with self.assertRaises(TypeError):
            makeExpressionByteCode(Ident("a"))
        with self.assertRaises(ValueError):
            self.vm.execute([BinaryOperation("+")])
        with self.assertRaises(ValueError):
            self.vm.execute([PushNumber(1), PushNumber(2), BinaryOperation("unknown")])
        with self.assertRaises(ZeroDivisionError):
            self.vm.execute(makeExpressionByteCode(Operation("/", Number(1), Number(0))))


if __name__ == "__main__":
    unittest.main()
