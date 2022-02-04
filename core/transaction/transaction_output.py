from __future__ import annotations

import struct
from typing import SupportsBytes, Dict, Any


class TransactionOutput(SupportsBytes):
    def __init__(self, address: bytes, amount: int | float):
        """
        Create a transaction output pointing to an address with an amount.

        :param address: the address to receive the coins
        :param amount: the amount to transfer
        """

        assert isinstance(address, bytes) and len(address) == 8, \
            'Provided `address` argument has to be of type bytes[8].'
        assert (isinstance(amount, float) or isinstance(amount, int)) and amount > 0, \
            'Provided `amount` argument has to be an int or a float > 0.'

        self.address = address
        self.amount = float(amount)

    def __bytes__(self):
        return self.address + struct.pack('>f', self.amount)

    def __eq__(self, other: Any):
        return bytes(other) == self.__bytes__()

    def __hash__(self):
        return hash(self.__bytes__())

    def json(self) -> Dict:
        return {
            'address': self.address.hex(),
            'amount': self.amount
        }

    @classmethod
    def from_bytes(cls, b: bytes) -> (bytes, TransactionOutput):
        assert isinstance(b, bytes), \
            'Provided `b` argument has to be of type bytes.'
        assert len(b) >= 8 + 4, \
            'Provided `b` argument cannot be deserialized.'

        b, address = b[8:], b[:8]
        b, amount = b[4:], struct.unpack('>f', b[:4])[0]

        return b, TransactionOutput(address, amount)
