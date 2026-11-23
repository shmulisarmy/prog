from __future__ import annotations

from dataclasses import field
import inspect
import unittest

from typeguard import TypeCheckError

from ast_ import ClassDef, Number, Operation, Type
from instructions import Allocate, JumpIfZero
from runtime_types import dataclass
from runtime_data_types import MemLocationKind, MemSlot
from vm import Vm
from source_range import Position, Range


position = Position("test.code", 1, 1)
DEBUG_LOCATION = dict(range=Range(position, position), created_at=__file__)


@dataclass
class NamedAllocate(Allocate):
    name: str = 'allocation'


@dataclass
class AllocationBatch:
    allocations: list[Allocate]
    next: AllocationBatch | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class FrozenBatch:
    amounts: list[int] = field(default_factory=list)


class RuntimeTypesTest(unittest.TestCase):
    def test_allocate(self):
        self.assertEqual(Allocate(123, **DEBUG_LOCATION).amount, 123)
        self.assertEqual(Allocate(amount=123, **DEBUG_LOCATION).amount, 123)
        self.assertEqual(inspect.signature(Allocate).parameters['amount'].default,
                         inspect.Parameter.empty)
        for value in ('hey', None, 12.5):
            with self.subTest(value=value), self.assertRaises(TypeCheckError):
                Allocate(value, **DEBUG_LOCATION)

    def test_nested_project_dataclasses_and_collections(self):
        self.assertEqual(Operation('+', Number(1), Number(2)).left, Number(1))
        self.assertEqual(Type('pointer', [Type('int')]).subtypes, [Type('int')])
        for construct in (
            lambda: Number('hey'),
            lambda: Operation('+', Number(1), 'hey'),
            lambda: Type('pointer', [Type('int'), 'hey']),
            lambda: MemSlot(0, 'heap', 1),
            lambda: AllocationBatch([Allocate(1, **DEBUG_LOCATION), 'hey']),
        ):
            with self.subTest(construct=construct), self.assertRaises(TypeCheckError):
                construct()
        self.assertEqual(MemSlot(0, MemLocationKind.heap, 1).size, 1)

    def test_inherited_fields(self):
        self.assertEqual(NamedAllocate(123, **DEBUG_LOCATION).name, 'allocation')
        for construct in (lambda: NamedAllocate('hey', **DEBUG_LOCATION), lambda: NamedAllocate(1, 2, **DEBUG_LOCATION)):
            with self.subTest(construct=construct), self.assertRaises(TypeCheckError):
                construct()

    def test_postponed_annotations_and_dataclass_options(self):
        batch = AllocationBatch([Allocate(1, **DEBUG_LOCATION)])
        self.assertIs(AllocationBatch([], batch).next, batch)
        with self.assertRaises(TypeCheckError):
            AllocationBatch([], 'hey')
        first, second = FrozenBatch(), FrozenBatch()
        self.assertIsNot(first.amounts, second.amounts)
        self.assertEqual(FrozenBatch(amounts=[1]).amounts, [1])
        with self.assertRaises(TypeCheckError):
            FrozenBatch(amounts=[1, 'hey'])
        self.assertIsNone(ClassDef([]).compilerData)
        self.assertEqual(Vm([]).instructionPtr, 0)
        self.assertEqual(Vm([JumpIfZero(2, **DEBUG_LOCATION)]).instructionPtr, 0)


if __name__ == '__main__':
    unittest.main()
