from __future__ import annotations

import struct
from typing import Dict, Any, Tuple


class TransactionOutput:
    def __init__(self, address: bytes, amount: int | float):
        """
        Create a transaction output pointing to an address with an amount.

        :param address: the address to receive the coins
        :param amount: the amount to transfer
        """

        assert isinstance(address, bytes) and len(address) == 8, \
            'Argument `address` has to be of type bytes[8].'
        assert (isinstance(amount, float) or isinstance(amount, int)) and amount > 0, \
            'Argument `amount` has to be of type int or float and greater than zero.'

        self.address = address
        self.amount = float(amount)

    def __bytes__(self):
        return self.address + struct.pack('>f', self.amount)

    def __eq__(self, other: Any):
        return bytes(other) == self.__bytes__()

    def __hash__(self):
        return hash(self.__bytes__())

    def json(self) -> Dict[str, Any]:
        """
        Get the serialized transaction output dumpable to JSON.

        :return: a dictionary containing all information about this output
        """

        return {
            'address': self.address.hex(),
            'amount': self.amount
        }

    @classmethod
    def from_bytes(cls, b: bytes) -> Tuple[bytes, TransactionOutput]:
        """
        Deserialize a transaction output from provided bytes.

        :param b: the serialized output bytes
        :return: a tuple containing the remaining bytes and the output
        """

        from core.helpers import BytesHelper

        with BytesHelper.load_safe(b):
            b, address = BytesHelper.load_raw_data(b, 8)
            b, amount = b[4:], struct.unpack('>f', b[:4])[0]

        return b, TransactionOutput(address, amount)
