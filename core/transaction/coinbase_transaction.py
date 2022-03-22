from __future__ import annotations

import struct
from typing import Tuple, TYPE_CHECKING

from .transaction import Transaction
from .transaction_output import TransactionOutput

if TYPE_CHECKING:
    from core.block import Block
    from core.helpers.bytes import BytesHelper


class CoinbaseTransaction(Transaction):
    def __init__(self, address: bytes):
        """
        Create a coinbase transaction that awards reward to specified address.

        :param address: the address to award reward to
        """

        super().__init__([], [TransactionOutput(address, 10)])

    def valid(self, latest_block: Block | None) -> bool:
        """
        Check if this transaction is valid in blockchain defined by it's latest block.

        :param latest_block: the latest block of the checked blockchain or None
        """

        from core.block import Block

        assert latest_block is None or isinstance(latest_block, Block), \
            'Argument `latest_block` has to be an instance of Block or None.'

        # Coinbase transaction is always valid
        return True

    @classmethod
    def from_bytes(cls, b: bytes) -> Tuple[bytes, CoinbaseTransaction]:
        """
        Deserialize a transaction from provided bytes.

        :param b: the serialized transaction bytes
        :return: a tuple containing the remaining bytes and the transaction
        """

        from . import TransactionInput, TransactionSignature

        # TODO: Refactor and change some assertions into exceptions due to user input
        assert isinstance(b, bytes), \
            'Provided `b` argument has to be of type bytes.'

        b, timestamp = b[8:], struct.unpack('>q', b[:8])
        b, inputs = BytesHelper.to_array(b, TransactionInput)

        assert len(inputs) == 0, \
            'Parsed input count of coinbase transaction has to be 0.'

        b, outputs = BytesHelper.to_array(b, TransactionOutput)

        assert len(outputs) == 1, \
            'Parsed output count of coinbase transaction has to be 1.'

        b, signatures = BytesHelper.to_array(b, TransactionSignature)

        transaction = CoinbaseTransaction(outputs[0].address)
        transaction.timestamp = timestamp

        return b, transaction
