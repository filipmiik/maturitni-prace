from __future__ import annotations

from typing import Dict, Any, Tuple

from .transaction_outpoint import TransactionOutpoint


class TransactionInput:
    def __init__(self, outpoint: TransactionOutpoint):
        """
        Create a transaction input referencing a transaction outpoint.

        :param outpoint: the referenced transaction outpoint
        """

        assert isinstance(outpoint, TransactionOutpoint), \
            'Argument `outpoint` has to be an instance of TransactionOutpoint.'

        self.outpoint = outpoint

    def __bytes__(self):
        return bytes(self.outpoint)

    def __eq__(self, other: Any):
        return bytes(other) == self.__bytes__()

    def __hash__(self):
        return hash(self.__bytes__())

    def json(self) -> Dict[str, Any]:
        """
        Get the serialized transaction input dumpable to JSON.

        :return: a dictionary containing all information about this input
        """

        return {
            'outpoint': self.outpoint.json()
        }

    @classmethod
    def from_bytes(cls, b: bytes) -> Tuple[bytes, TransactionInput]:
        """
        Deserialize a transaction input from provided bytes.

        :param b: the serialized input bytes
        :return: a tuple containing the remaining bytes and the input
        """

        from ..helpers import BytesHelper

        with BytesHelper.load_safe(b):
            b, outpoint = TransactionOutpoint.from_bytes(b)

        return b, TransactionInput(outpoint)
