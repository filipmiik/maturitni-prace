from __future__ import annotations

from typing import SupportsBytes, Dict, Any

from .transaction_outpoint import TransactionOutpoint


class TransactionInput(SupportsBytes):
    def __init__(self, outpoint: TransactionOutpoint):
        """
        Create a transaction input referencing a transaction outpoint.

        :param outpoint: the referenced transaction outpoint
        """

        assert isinstance(outpoint, TransactionOutpoint), \
            'Provided `outpoint` argument has to be an instance of TransactionOutpoint.'

        self.outpoint = outpoint

    def __bytes__(self):
        return bytes(self.outpoint)

    def __eq__(self, other: Any):
        return bytes(other) == self.__bytes__()

    def __hash__(self):
        return hash(self.__bytes__())

    def json(self) -> Dict:
        return {
            'outpoint': self.outpoint.json()
        }

    @classmethod
    def from_bytes(cls, b: bytes) -> (bytes, TransactionInput):
        assert isinstance(b, bytes), \
            'Provided `b` argument has to be of type bytes.'

        b, outpoint = TransactionOutpoint.from_bytes(b)

        return b, TransactionInput(outpoint)
