from __future__ import annotations

import struct
from collections import defaultdict
from contextlib import suppress
from hashlib import sha256
from math import ceil
from time import time
from typing import Sequence, Dict, Tuple, List, Any, TYPE_CHECKING

from core import bytetools

if TYPE_CHECKING:
    from core.transaction import Transaction, CoinbaseTransaction, TransactionOutpoint, TransactionOutput


class Block:
    def __init__(self, previous_block: Block | None, transactions: Sequence[Transaction]):
        """
        Create a new block.

        :param previous_block: an instance of the previous block or none if genesis block
        :param transactions: a sequence of all transactions that a block should include
        """

        from core.block import GenesisBlock
        from core.transaction import Transaction, CoinbaseTransaction

        assert isinstance(previous_block, Block) or isinstance(self, GenesisBlock), \
            'Provided `previous_block` argument has to be an instance of Block.'
        assert isinstance(transactions, Sequence) \
               and all(isinstance(transaction, Transaction) for transaction in transactions), \
            'Provided `transactions` argument has to be a sequence of valid Transaction instances.'
        assert sum(isinstance(transaction, CoinbaseTransaction) for transaction in transactions) == 1, \
            'Provided transactions must include one and only one instance of CoinbaseTransaction.'

        self.previous_block = previous_block
        self.transactions = tuple(transactions)
        self.timestamp = ceil(time() * 1000)
        self.nonce = 0

    def __bytes__(self):
        return b''.join([
            self.block_header(),
            bytetools.bytes_from_array(self.transactions),
        ])

    def __eq__(self, other: Any):
        return bytes(other) == self.__bytes__()

    def __hash__(self):
        return hash(self.__bytes__())

    def id(self) -> bytes:
        return sha256(self.block_header()).digest()

    def block_header(self) -> bytes:
        from core.transaction import Transaction

        return b''.join([
            self.previous_block.id(),
            Transaction.calculate_merkle_root(self.transactions),
            struct.pack('>q', self.timestamp),
            struct.pack('>q', self.nonce)
        ])

    def json(self) -> Dict:
        from core.transaction import Transaction

        return {
            'previous_block_id': self.previous_block.id().hex(),
            'transactions_root': Transaction.calculate_merkle_root(self.transactions).hex(),
            'timestamp': self.timestamp,
            'nonce': self.nonce,
            'transactions': tuple(transaction.json() for transaction in self.transactions)
        }

    def unspent_outpoints(self, addresses: Sequence[bytes] = None) -> Dict[TransactionOutpoint, TransactionOutput]:
        assert addresses is None or all(isinstance(address, bytes) and len(address) == 8 for address in addresses), \
            'Addresses must be a sequence of bytes[8].'

        from core.transaction import TransactionOutpoint

        transactions = self.expand_transactions()
        unspent_outpoints: Dict[TransactionOutpoint, TransactionOutput] = {}

        for transaction in transactions.values():
            for tx_input in transaction.inputs:
                # KeyErrors are going to be raised in case that 'addresses' argument is provided
                # This function should be executed only on checked blockchain, so suppressing the exception is safe
                with suppress(KeyError):
                    del unspent_outpoints[tx_input.outpoint]

            for i, tx_output in enumerate(transaction.outputs):
                if addresses is None or tx_output.address in addresses:
                    unspent_outpoints[TransactionOutpoint(transaction.id(), i)] = tx_output

        return unspent_outpoints

    def balances(self, unspent_outpoints: Dict[TransactionOutpoint, TransactionOutput]) -> Dict:
        from core.transaction import TransactionOutpoint, TransactionOutput

        assert isinstance(unspent_outpoints, dict) \
               and all(isinstance(outpoint, TransactionOutpoint) and isinstance(amount, TransactionOutput)
                       for outpoint, amount in unspent_outpoints.items()), \
            'Unspent outpoints have to be a Dict[TransactionOutpoint, TransactionOutput].'

        balances = defaultdict(lambda: 0)

        for outpoint, tx_output in unspent_outpoints.items():
            balances[tx_output.address] += tx_output.amount

        return balances

    def clone(self) -> Block:
        block = Block(self.previous_block, self.transactions)
        block.timestamp = self.timestamp
        block.nonce = self.nonce

        return block

    def valid(self, shallow: bool = True) -> bool:
        return self.valid_proof(shallow) and self.valid_transactions(shallow)

    def valid_proof(self, shallow: bool = True) -> bool:
        # Expand the blockchain to check all blocks if needed
        blocks = (self,) if shallow else self.expand_chain()

        # Iterate over blocks:
        for block in blocks:
            # Check if proof is valid
            if block.id() >= (bytes(2) + b'\xff' * 30):
                return False

        return True

    def valid_transactions(self, shallow: bool = True) -> bool:
        # Expand the blockchain to check transactions per-block if needed
        blocks = (self,) if shallow else self.expand_chain()

        # Iterate over blocks
        for block in blocks:
            transactions = block.transactions

            # Check if all transactions are valid
            if any(not transaction.valid(block.previous_block) for transaction in transactions):
                return False

        return True

    def expand_chain(self) -> Tuple[Block]:
        blocks: List[Block] = [self]

        while isinstance(block := blocks[-1].previous_block, Block):
            blocks.append(block)

        return tuple(blocks[::-1])

    def expand_transactions(self) -> Dict[bytes, Transaction]:
        transactions = {}

        for block in self.expand_chain():
            for transaction in block.transactions:
                transactions[transaction.id()] = transaction

        return transactions

    @classmethod
    def from_bytes(cls, b: bytes, previous_block: Block) -> (bytes, Block):
        from core.transaction import Transaction

        assert isinstance(b, bytes), \
            'Provided `b` argument has to be of type bytes.'

        b, previous_block_id = b[32:], b[:32]

        assert previous_block.id() == previous_block_id, \
            'Provided `previous_block` has to match previous block ID from `b` bytes.'

        b, merkle_root = b[32:], b[:32]
        b, timestamp = b[8:], struct.unpack('>q', b[:8])[0]
        b, nonce = b[8:], struct.unpack('>q', b[:8])[0]

        b, transactions = bytetools.array_from_bytes(b, Transaction)

        assert merkle_root == Transaction.calculate_merkle_root(transactions), \
            'Calculated merkle root from parsed transactions has to match parsed merkle root.'

        block = Block(previous_block, transactions)
        block.timestamp = timestamp
        block.nonce = nonce

        return b, block
