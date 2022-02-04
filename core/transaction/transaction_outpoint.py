from __future__ import annotations

import struct
from typing import SupportsBytes, Dict, Any


class TransactionOutpoint(SupportsBytes):
    def __init__(self, transaction_id: bytes, output_index: int):
        """
        Create representation of transaction outpoint consisting of transaction and specific output of that transaction.

        :param transaction_id: the ID of the referenced transaction
        :param output_index: the referenced transaction output
        """

        assert isinstance(transaction_id, bytes) and len(transaction_id) == 32, \
            'Provided `transaction_id` argument has to be of type bytes[32].'
        assert isinstance(output_index, int) and output_index >= 0, \
            'Provided `output_index` argument has to be a positive integer or 0.'

        self.transaction_id = transaction_id
        self.output_index = output_index

    def __bytes__(self):
        return self.transaction_id + struct.pack('>H', self.output_index)

    def __eq__(self, other: Any):
        return bytes(other) == self.__bytes__()

    def __hash__(self):
        return hash(self.__bytes__())

    def json(self) -> Dict:
        return {
            'transaction_id': self.transaction_id.hex(),
            'output_index': self.output_index
        }

    @classmethod
    def from_bytes(cls, b: bytes) -> (bytes, TransactionOutpoint):
        assert isinstance(b, bytes), \
            'Provided `b` argument has to be of type bytes.'
        assert len(b) >= 32 + 2, \
            'Provided `b` argument cannot be deserialized.'

        b, transaction_id = b[32:], b[:32]
        b, output_index = b[2:], struct.unpack('>H', b[:2])[0]

        return b, TransactionOutpoint(transaction_id, output_index)
