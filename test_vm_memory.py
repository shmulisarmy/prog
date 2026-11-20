import unittest

from instructions import PlaceStackMemoryIntoSlot, PushNumber
from runtime_data_types import MemLocationKind, MemSlot
from vm import Stackframe, Vm


class VMMemoryTest(unittest.TestCase):
    def test_place_stack_memory_into_slot(self):
        self.vm = Vm()
        self.vm.stackframes = [Stackframe(1, None)]
        for size in (0, 1, 2):
            with self.subTest(size=size):
                values = [7, 8][:size]
                slot = MemSlot(1, MemLocationKind.local_, size)
                instructions = [PushNumber(n) for n in [99, 10, 0, 0, 20] + values]
                instructions.append(PlaceStackMemoryIntoSlot(slot))
                expected = [99, 10, 0, 0, 20]
                expected[2:2 + size] = values
                self.assertEqual(self.vm.execute(instructions), expected)


if __name__ == "__main__":
    unittest.main()
