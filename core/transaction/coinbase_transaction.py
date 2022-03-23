from __future__ import annotations

import struct
from typing import Tuple, TYPE_CHECKING, Sequence

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

    def valid(self, latest_block: Block | None, additional_transactions: Sequence[Transaction] = ()) -> bool:
        """
        Check if this transaction is valid in blockchain defined by it's latest block.

        :param latest_block: the latest block of the checked blockchain or None
        :param additional_transactions: additional out-of-block transactions to while validating
        """

        from core.block import Block

        assert latest_block is None or isinstance(latest_block, Block), \
            'Argument `latest_block` has to be an instance of Block or None.'
        assert all(isinstance(tx, Transaction) for tx in additional_transactions), \
            'Argument `additional_transactions` has to be a sequence of Transaction instances.'

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

        with BytesHelper.load_safe(b):
            # Load transaction properties
            b, timestamp = b[8:], struct.unpack('>q', b[:8])
            b, inputs = BytesHelper.to_array(b, TransactionInput)

            if len(inputs) != 0:
                raise ValueError('Loaded coinbase transaction cannot contain any inputs.')

            b, outputs = BytesHelper.to_array(b, TransactionOutput)

            if len(outputs) != 1:
                raise ValueError('Loaded coinbase transaction must contain only one output.')

            b, signatures = BytesHelper.to_array(b, TransactionSignature)

        # Create the transaction
        transaction = CoinbaseTransaction(outputs[0].address)
        transaction.timestamp = timestamp

        return b, transaction
