from dataclasses import field
from source_range import Range
from runtime_types import dataclass


@dataclass
class ClassReturn:
    range: Range = field(kw_only=True, compare=False)
    created_at: str = field(kw_only=True, compare=False)
    pass
