from ast_ import ClassDef, ClassDefCompilerData, ScopeInfo
from compilerTools import getTypeSize
from runtime_data_types import MemLocationKind, MemSlot


def assignFieldOffsets(self: ClassDef):
        assert not self.compilerData, "cant do it twice"
        self.compilerData = ClassDefCompilerData()
        current = 0
        for field in self.fields:
            size = getTypeSize(field.type_, scopeInfo=ScopeInfo(self))
            field.compileTimeInfo_memSlot = MemSlot(memLocationKind = MemLocationKind.NA, memOffset = current, size=size)
            current += size
        self.compilerData.memSlotUpto = current