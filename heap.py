"""Slot-based heap storage for the VM, independent of stack frames."""

from runtime_data_types import MemLocationKind, MemSlot


class Heap:
    """Own allocations until explicitly freed.

    Sizes are positive slot counts. New slots contain None. Only whole
    allocations may be freed or resized; read/write also accept field slots.
    Always use the slot returned by reallocate. Offset-only slots cannot
    detect stale pointers once their addresses have been reused, or distinguish
    matching addresses belonging to different Heap instances.
    """

    def __init__(self):
        self._memory: list[object] = []
        self._allocations: dict[int, int] = {}
        self._free_ranges: list[tuple[int, int]] = []

    def allocate(self, size: int) -> MemSlot:
        self._validate_size(size)
        for index, (offset, available) in enumerate(self._free_ranges):
            if available >= size:
                if available == size:
                    del self._free_ranges[index]
                else:
                    self._free_ranges[index] = (offset + size, available - size)
                break
        else:
            offset = len(self._memory)
            self._memory.extend([None] * size)
        self._allocations[offset] = size
        return MemSlot(offset, MemLocationKind.heap, size)

    def reallocate(self, memSlot: MemSlot, newSize: int) -> MemSlot:
        self._validate_allocation(memSlot)
        self._validate_size(newSize)
        offset, oldSize = memSlot.memOffset, memSlot.size
        end = offset + oldSize
        if newSize < oldSize:
            self._release(offset + newSize, oldSize - newSize)
        elif newSize > oldSize:
            extra = newSize - oldSize
            for index, (start, available) in enumerate(self._free_ranges):
                if start == end and available >= extra:
                    if available == extra:
                        del self._free_ranges[index]
                    else:
                        self._free_ranges[index] = (start + extra, available - extra)
                    break
            else:
                if end == len(self._memory):
                    self._memory.extend([None] * extra)
                else:
                    # Allocate first so allocation failure preserves the old block.
                    replacement = self.allocate(newSize)
                    self._memory[replacement.memOffset:replacement.memOffset + oldSize] = self._memory[offset:end]
                    self.free(memSlot)
                    return replacement
        self._allocations[offset] = newSize
        return MemSlot(offset, MemLocationKind.heap, newSize)

    def free(self, memSlot: MemSlot) -> None:
        self._validate_allocation(memSlot)
        self._release(memSlot.memOffset, memSlot.size)
        del self._allocations[memSlot.memOffset]

    def read(self, memSlot: MemSlot) -> list[object]:
        """Return a copy of the values in a live allocation or field slot."""
        self._validate_access(memSlot)
        return self._memory[memSlot.memOffset:memSlot.memOffset + memSlot.size]

    def write(self, memSlot: MemSlot, values: list[object]) -> None:
        self._validate_access(memSlot)
        if len(values) != memSlot.size:
            raise ValueError("Value count must match the slot size")
        self._memory[memSlot.memOffset:memSlot.memOffset + memSlot.size] = values

    @staticmethod
    def _validate_size(size: int) -> None:
        if type(size) is not int or size <= 0:
            raise ValueError("Size must be a positive integer slot count")

    def _validate_slot(self, memSlot: MemSlot) -> None:
        if not isinstance(memSlot, MemSlot):
            raise TypeError("Expected a MemSlot")
        if memSlot.memLocationKind != MemLocationKind.heap:
            raise ValueError("Expected a heap memory slot")
        if type(memSlot.memOffset) is not int or memSlot.memOffset < 0:
            raise ValueError("Invalid heap offset")
        self._validate_size(memSlot.size)

    def _validate_allocation(self, memSlot: MemSlot) -> None:
        self._validate_slot(memSlot)
        if self._allocations.get(memSlot.memOffset) != memSlot.size:
            raise ValueError("Expected the whole slot of a live allocation")

    def _validate_access(self, memSlot: MemSlot) -> None:
        self._validate_slot(memSlot)
        # ponytail: linear scan; index allocation ranges if heap access becomes a bottleneck.
        for offset, size in self._allocations.items():
            if offset <= memSlot.memOffset and memSlot.memOffset + memSlot.size <= offset + size:
                return
        raise ValueError("Slot is outside a live heap allocation")

    def _release(self, offset: int, size: int) -> None:
        self._memory[offset:offset + size] = [None] * size
        self._free_ranges.append((offset, size))
        self._free_ranges.sort()
        merged: list[tuple[int, int]] = []
        for start, length in self._free_ranges:
            if merged and merged[-1][0] + merged[-1][1] == start:
                previous, previous_size = merged[-1]
                merged[-1] = (previous, previous_size + length)
            else:
                merged.append((start, length))
        self._free_ranges = merged
