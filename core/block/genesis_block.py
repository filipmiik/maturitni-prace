from __future__ import annotations

import struct
from typing import Sequence, Dict, TYPE_CHECKING, Tuple, Any

from .block import Block
from ..helpers.bytes import BytesHelper

if TYPE_CHECKING:
    from core.transaction import Transaction


class GenesisBlock(Block):
    def __init__(self, transactions: Sequence[Transaction]):
        super().__init__(None, transactions)

    def block_header(self) -> bytes:
        """
        Get the serialized block header.

        :return: the serialized block header
        """

        from core.transaction import Transaction

        return b''.join([
            bytes(32),
            Transaction.calculate_merkle_root(self.transactions),
            struct.pack('>q', self.timestamp),
            struct.pack('>q', self.nonce)
        ])

    def json(self) -> Dict[str, Any]:
        """
        Get the serialized block dumpable to JSON.

        :return: a dictionary containing all information about this block
        """

        from core.transaction import Transaction

        return {
            'previous_block_id': None,
            'transactions_root': Transaction.calculate_merkle_root(self.transactions).hex(),
            'timestamp': self.timestamp,
            'nonce': self.nonce,
            'transactions': tuple(transaction.json() for transaction in self.transactions)
        }

    @classmethod
    def from_bytes(cls, b: bytes, previous_block: None = None) -> Tuple[bytes, GenesisBlock]:
        """
        Deserialize a genesis block from provided bytes.

        :param b: the serialized genesis block bytes
        :param previous_block: None
        :return: a tuple containing the remaining bytes and the deserialized genesis block
        """

        from core.transaction import Transaction

        # TODO: Refactor and change some assertions into exceptions due to user input
        assert isinstance(b, bytes), \
            'Provided `b` argument has to be of type bytes.'

        b, previous_block_id = b[32:], b[:32]

        assert previous_block_id == bytes(32), \
            'Parsed previous block ID of genesis block has to be empty bytes[32].'

        b, merkle_root = b[32:], b[:32]
        b, timestamp = b[8:], struct.unpack('>q', b[:8])[0]
        b, nonce = b[8:], struct.unpack('>q', b[:8])[0]

        b, transactions = BytesHelper.to_array(b, Transaction)

        assert merkle_root == Transaction.calculate_merkle_root(transactions), \
            'Calculated merkle root from parsed transactions has to match parsed merkle root.'

        block = GenesisBlock(transactions)
        block.timestamp = timestamp
        block.nonce = nonce

        return b, block

    @classmethod
    def from_bytes_chain(cls, b: bytes) -> Block:
        """
        Deserialize an expanded blockchain from provided bytes..

        :param b: the serialized blockchain bytes
        :return: an instance of the latest block in the blockchain
        """

        assert isinstance(b, bytes), \
            'Argument `b` has to be of type bytes.'

        # Deserialize first block as a genesis block
        b, block = cls.from_bytes(b, None)

        # Loop and deserialize bytes until there are no left
        while len(b) > 0:
            b, block = Block.from_bytes(b, block)

        return block
