import unittest
from unittest.mock import patch

from heap import Heap
from runtime_data_types import MemLocationKind, MemSlot


class HeapTest(unittest.TestCase):
    def test_allocate_write_and_field_access(self):
        heap = Heap()
        slot = heap.allocate(3)
        self.assertEqual(slot, MemSlot(0, MemLocationKind.heap, 3))
        self.assertEqual(heap.read(slot), [None, None, None])
        heap.write(slot, [10, 20, 30])
        field = MemSlot(1, MemLocationKind.heap, 1)
        heap.write(field, [99])
        self.assertEqual(heap.read(field), [99])
        values = heap.read(slot)
        values[0] = 0
        self.assertEqual(heap.read(slot), [10, 99, 30])

    def test_free_merges_neighbors_and_allocate_splits_space(self):
        heap = Heap()
        first, second, third = [heap.allocate(2) for _ in range(3)]
        heap.write(second, [4, 5])
        heap.free(first)
        heap.free(third)
        heap.free(second)
        large = heap.allocate(5)
        remaining = heap.allocate(1)
        self.assertEqual((large.memOffset, remaining.memOffset), (0, 5))
        self.assertEqual(heap.read(large), [None] * 5)

    def test_reallocate_shrinks_and_reuses_tail(self):
        heap = Heap()
        original = heap.allocate(4)
        heap.write(original, [1, 2, 3, 4])
        smaller = heap.reallocate(original, 2)
        self.assertEqual(heap.read(smaller), [1, 2])
        self.assertEqual(original.size, 4)
        tail = heap.allocate(2)
        self.assertEqual(tail.memOffset, 2)
        self.assertEqual(heap.read(tail), [None, None])

    def test_reallocate_grows_at_end_and_into_free_neighbor(self):
        heap = Heap()
        slot = heap.allocate(1)
        heap.write(slot, [7])
        slot = heap.reallocate(slot, 2)
        self.assertEqual(heap.read(slot), [7, None])
        neighbor = heap.allocate(3)
        blocker = heap.allocate(1)
        heap.write(blocker, [42])
        heap.free(neighbor)
        slot = heap.reallocate(slot, 4)
        self.assertEqual(slot.memOffset, 0)
        self.assertEqual(heap.read(slot), [7, None, None, None])
        self.assertEqual(heap.allocate(1).memOffset, 4)
        self.assertEqual(heap.read(blocker), [42])

    def test_reallocate_moves_and_preserves_values(self):
        heap = Heap()
        original = heap.allocate(2)
        blocker = heap.allocate(1)
        heap.write(original, [8, 9])
        heap.write(blocker, [10])
        same = heap.reallocate(original, 2)
        self.assertEqual(same, original)
        self.assertIsNot(same, original)
        moved = heap.reallocate(original, 4)
        self.assertNotEqual(moved.memOffset, original.memOffset)
        self.assertEqual(heap.read(moved), [8, 9, None, None])
        self.assertEqual(heap.read(blocker), [10])
        with self.assertRaises(ValueError):
            heap.read(original)
        self.assertEqual(heap.allocate(2).memOffset, original.memOffset)

    def test_failed_reallocate_keeps_original(self):
        heap = Heap()
        slot = heap.allocate(1)
        heap.allocate(1)
        heap.write(slot, [7])
        with patch.object(heap, "allocate", side_effect=MemoryError):
            with self.assertRaises(MemoryError):
                heap.reallocate(slot, 3)
        self.assertEqual(heap.read(slot), [7])

    def test_invalid_operations(self):
        heap = Heap()
        slot = heap.allocate(2)
        heap.allocate(1)
        for size in (0, -1, 1.5, True):
            with self.subTest(size=size):
                with self.assertRaises(ValueError):
                    heap.allocate(size)
                with self.assertRaises(ValueError):
                    heap.reallocate(slot, size)
        for invalid in (
            MemSlot(0, MemLocationKind.AbsoluteStackPosition, 2),
            MemSlot(1, MemLocationKind.heap, 1),  # Field pointer.
            MemSlot(0, MemLocationKind.heap, 3),  # Spans two allocations.
            MemSlot(-1, MemLocationKind.heap, 2),
        ):
            with self.subTest(slot=invalid):
                with self.assertRaises(ValueError):
                    heap.free(invalid)
                with self.assertRaises(ValueError):
                    heap.reallocate(invalid, 4)
        with self.assertRaises(ValueError):
            heap.read(MemSlot(1, MemLocationKind.heap, 2))
        with self.assertRaises(ValueError):
            heap.write(slot, [1])
        with self.assertRaises(TypeError):
            heap.free(None)
        heap.free(slot)
        for operation in (heap.read, heap.free):
            with self.assertRaises(ValueError):
                operation(slot)
        with self.assertRaises(ValueError):
            heap.reallocate(slot, 1)


if __name__ == "__main__":
    unittest.main()
