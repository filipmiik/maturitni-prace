import struct
from typing import Tuple, TypeVar, Sequence, SupportsBytes, List

T = TypeVar('T')


def bytes_from_array(array: Sequence[SupportsBytes]) -> bytes:
    assert all(isinstance(item, SupportsBytes) for item in array), \
        'Provided `array` argument has to be a sequence of SupportsBytes.'

    array_len = struct.pack('>H', len(array))
    items = b''.join(list(bytes(item) for item in array))

    return array_len + items


def array_from_bytes(b: bytes, cls: T) -> (bytes, Tuple[T]):
    # TODO: Create custom SupportsFromBytes class and assert cls argument
    assert isinstance(b, bytes), \
        'Provided `b` argument has to be of type bytes.'
    assert len(b) >= 2, \
        'Provided `b` argument is not deserializable as an array.'

    b, array_len = b[2:], struct.unpack('>H', b[:2])[0]
    items: List[T] = []

    for _ in range(array_len):
        b, item = cls.from_bytes(b)
        items.append(item)

    return b, tuple(items)
