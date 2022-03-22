from __future__ import annotations

import struct
from typing import runtime_checkable, Protocol, TypeVar, Tuple, SupportsBytes, List, Iterable, Type


@runtime_checkable
class SupportsFromBytes(Protocol):
    @classmethod
    def from_bytes(cls, b: bytes) -> Tuple[bytes, SupportsFromBytes]:
        pass


T = TypeVar('T', bound=SupportsFromBytes)


class BytesHelper:
    @staticmethod
    def to_array(b: bytes, cls: Type[T]) -> Tuple[bytes, Tuple[T]]:
        """
        Convert provided bytes to array of provided objects.

        :param b: a byte sequence in format "length[>H] + items[bytes(T)]"
        :param cls: a class implementing the SupportsFromBytes protocol
        :return: a tuple of remaining bytes and a tuple of deserialized classes
        """

        assert isinstance(b, bytes), \
            'Argument `b` has to be of type bytes.'
        assert isinstance(cls, SupportsFromBytes), \
            'Argument `cls` has to be an object[SupportsFromBytes].'

        # Read bytes and unpack them to get array length, then delete the read bytes
        try:
            b, array_len = b[2:], struct.unpack('>H', b[:2])[0]
        except struct.error:
            raise ValueError('Argument `b` is not deserializable as an array.')

        # Load items from unread bytes and delete the read bytes on every iteration
        items: List[T] = list()

        for _ in range(array_len):
            b, item = cls.from_bytes(b)
            items.append(item)

        return b, tuple(items)

    @staticmethod
    def from_array(array: Iterable) -> bytes:
        """
        Convert provided array to bytes.

        :param array: an iterable of objects that implement the SupportsBytes protocol
        :return: a byte sequence in format "length[>H] + items[bytes(T)]"
        """

        assert all(isinstance(cls, SupportsBytes) for cls in array), \
            'Argument `array` has to be an iterable of object[SupportsBytes].'

        # Serialize every item and join them together forming one long bytes object
        array_len = 0
        items = b''

        for item in array:
            array_len += 1
            items += bytes(item)

        # Serialize the array length
        array_len = struct.pack('>H', array_len)

        return array_len + items
