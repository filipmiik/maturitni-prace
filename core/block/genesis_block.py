from __future__ import annotations

import struct
from typing import Sequence, Dict, TYPE_CHECKING

from .block import Block
from .. import bytetools

if TYPE_CHECKING:
    from core.transaction import Transaction


class GenesisBlock(Block):
    def __init__(self, transactions: Sequence[Transaction]):
        super().__init__(None, transactions)

    def block_header(self) -> bytes:
        from core.transaction import Transaction

        return b''.join([
            bytes(32),
            Transaction.calculate_merkle_root(self.transactions),
            struct.pack('>q', self.timestamp),
            struct.pack('>q', self.nonce)
        ])

    def json(self) -> Dict:
        from core.transaction import Transaction

        return {
            'previous_block_id': None,
            'transactions_root': Transaction.calculate_merkle_root(self.transactions).hex(),
            'timestamp': self.timestamp,
            'nonce': self.nonce,
            'transactions': tuple(transaction.json() for transaction in self.transactions)
        }

    def clone(self) -> GenesisBlock:
        block = GenesisBlock(self.transactions)
        block.timestamp = self.timestamp
        block.nonce = self.nonce

        return block

    @classmethod
    def from_bytes(cls, b: bytes, previous_block: None) -> (bytes, GenesisBlock):
        from core.transaction import Transaction

        assert isinstance(b, bytes), \
            'Provided `b` argument has to be of type bytes.'

        b, previous_block_id = b[32:], b[:32]

        assert previous_block_id == bytes(32), \
            'Parsed previous block ID of genesis block has to be empty bytes[32].'

        b, merkle_root = b[32:], b[:32]
        b, timestamp = b[8:], struct.unpack('>q', b[:8])[0]
        b, nonce = b[8:], struct.unpack('>q', b[:8])[0]

        b, transactions = bytetools.array_from_bytes(b, Transaction)

        assert merkle_root == Transaction.calculate_merkle_root(transactions), \
            'Calculated merkle root from parsed transactions has to match parsed merkle root.'

        block = GenesisBlock(transactions)
        block.timestamp = timestamp
        block.nonce = nonce

        return b, block

    @classmethod
    def from_bytes_chain(cls, b: bytes) -> Block:
        assert isinstance(b, bytes), \
            'Provided `b` argument has to be of type bytes.'

        b, block = cls.from_bytes(b, None)

        while len(b) > 0:
            b, block = Block.from_bytes(b, block)

        return block
