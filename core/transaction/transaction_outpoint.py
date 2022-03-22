from __future__ import annotations

import struct
from typing import Dict, Any, Tuple


class TransactionOutpoint:
    def __init__(self, transaction_id: bytes, output_index: int):
        """
        Create representation of transaction outpoint consisting of transaction and specific output of that transaction.

        :param transaction_id: the ID of the referenced transaction
        :param output_index: the referenced transaction output
        """

        assert isinstance(transaction_id, bytes) and len(transaction_id) == 32, \
            'Argument `transaction_id` has to be of type bytes[32].'
        assert isinstance(output_index, int) and output_index >= 0, \
            'Argument `output_index` has to be of type int greater or equal to zero.'

        self.transaction_id = transaction_id
        self.output_index = output_index

    def __bytes__(self):
        return self.transaction_id + struct.pack('>H', self.output_index)

    def __eq__(self, other: Any):
        return bytes(other) == self.__bytes__()

    def __hash__(self):
        return hash(self.__bytes__())

    def json(self) -> Dict[str, Any]:
        """
        Get the serialized transaction outpoint dumpable to JSON.

        :return: a dictionary containing all information about this outpoint
        """

        return {
            'transaction_id': self.transaction_id.hex(),
            'output_index': self.output_index
        }

    @classmethod
    def from_bytes(cls, b: bytes) -> Tuple[bytes, TransactionOutpoint]:
        """
        Deserialize a transaction outpoint from provided bytes.

        :param b: the serialized outpoint bytes
        :return: a tuple containing the remaining bytes and the outpoint
        """

        from core.helpers import BytesHelper

        with BytesHelper.load_safe(b):
            b, transaction_id = BytesHelper.load_raw_data(b, 32)
            b, output_index = b[2:], struct.unpack('>H', b[:2])[0]

        return b, TransactionOutpoint(transaction_id, output_index)
