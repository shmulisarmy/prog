import unittest

from instructions import PlaceStackMemoryIntoSlot, PushNumber
from runtime_data_types import MemLocationKind, MemSlot
from vm import Stackframe, Vm
from source_range import Position, Range


position = Position('test.code', 1, 1)
DEBUG_LOCATION = dict(range=Range(position, position), created_at=__file__)


class VMMemoryTest(unittest.TestCase):
    def test_place_stack_memory_into_slot(self):
        for size in (0, 1, 2):
            with self.subTest(size=size):
                values = [7, 8][:size]
                slot = MemSlot(1, MemLocationKind.local_, size)
                instructions = [PushNumber(n, **DEBUG_LOCATION) for n in [99, 10, 0, 0, 20] + values]
                instructions.append(PlaceStackMemoryIntoSlot(slot, **DEBUG_LOCATION))
                vm = Vm(instructions)
                vm.stackframes = [Stackframe(1, None)]
                expected = [99, 10, 0, 0, 20]
                expected[2:2 + size] = values
                vm.execute()
                self.assertEqual(vm.stack, expected)


if __name__ == "__main__":
    unittest.main()
