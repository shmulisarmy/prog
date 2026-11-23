import unittest

from instructions import OffsetPointer, LoadMemoryFromSlot, PlaceAbsoluteMemSlotOnStack
from runtime_data_types import MemLocationKind, MemSlot
from vm import Stackframe, Vm
from source_range import Position, Range


position = Position("test.code", 1, 1)
DEBUG_LOCATION = dict(range=Range(position, position), created_at=__file__)


class VMPointerTest(unittest.TestCase):
    def test_field_address_preserves_original_pointer(self):
        for offset in (0, 1):
            with self.subTest(offset=offset):
                instructions = [
                    PlaceAbsoluteMemSlotOnStack(MemSlot(4, MemLocationKind.local_, 2), **DEBUG_LOCATION),
                    LoadMemoryFromSlot(MemSlot(0, MemLocationKind.local_, 1), **DEBUG_LOCATION),
                    OffsetPointer(offset, 1, **DEBUG_LOCATION),
                ]
                vm = Vm(instructions)
                vm.instructionPtr = 0
                vm.stackframes = [Stackframe(0, None)]
                vm.execute()

                original, field = vm.stack
                self.assertEqual(original, MemSlot(4, MemLocationKind.AbsoluteStackPosition, 2))
                self.assertEqual(field, MemSlot(4 + offset, MemLocationKind.AbsoluteStackPosition, 1))
                self.assertIsNot(original, field)


if __name__ == '__main__':
    unittest.main()
