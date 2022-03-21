from __future__ import annotations

import struct

from .transaction import Transaction
from .transaction_output import TransactionOutput
from .. import bytetools
from ..block import Block


class CoinbaseTransaction(Transaction):
    def __init__(self, address: bytes):
        super().__init__([], [TransactionOutput(address, 10)])

    def valid(self, latest_block: Block | None) -> bool:
        assert latest_block is None or isinstance(latest_block, Block), \
            'Latest block must be an instance of Block or None.'

        # Coinbase transaction is always valid
        return True

    @classmethod
    def from_bytes(cls, b: bytes) -> (bytes, CoinbaseTransaction):
        from . import TransactionInput, TransactionSignature

        assert isinstance(b, bytes), \
            'Provided `b` argument has to be of type bytes.'

        b, timestamp = b[8:], struct.unpack('>q', b[:8])
        b, inputs = bytetools.array_from_bytes(b, TransactionInput)

        assert len(inputs) == 0, \
            'Parsed input count of coinbase transaction has to be 0.'

        b, outputs = bytetools.array_from_bytes(b, TransactionOutput)

        assert len(outputs) == 1, \
            'Parsed output count of coinbase transaction has to be 1.'

        b, = bytetools.array_from_bytes(b, TransactionSignature)

        transaction = CoinbaseTransaction(outputs[0].address)
        transaction.timestamp = timestamp

        return b, transaction
