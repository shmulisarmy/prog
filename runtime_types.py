"""Standard dataclasses with automatic Typeguard validation at construction.

Typeguard's source instrumentation cannot find dataclass-generated __init__
methods. Check the initialized fields instead, including defaults and inherited
fields. As with ordinary dataclasses, later attribute mutation is unrestricted.
"""

from dataclasses import dataclass as std_dataclass, field, fields
from functools import cache, wraps
from typing import dataclass_transform, get_type_hints

from typeguard import CollectionCheckStrategy, TypeCheckError, check_type


@cache
def _field_types(cls):
    # Resolve lazily: AST annotations refer to classes/aliases declared later.
    hints = get_type_hints(cls)
    return tuple((f.name, hints[f.name]) for f in fields(cls))


@dataclass_transform(field_specifiers=(field,))
def dataclass(cls=None, **options):
    def decorate(cls):
        cls = std_dataclass(cls, **options)
        init = cls.__init__

        @wraps(init)
        def checked_init(self, *args, **kwargs):
            init(self, *args, **kwargs)
            for name, hint in _field_types(cls):
                try:
                    check_type(getattr(self, name), hint,
                               collection_check_strategy=CollectionCheckStrategy.ALL_ITEMS)
                except TypeCheckError as error:
                    error.append_path_element(f'{cls.__qualname__}.{name}')
                    raise

        cls.__init__ = checked_init
        return cls

    return decorate if cls is None else decorate(cls)
