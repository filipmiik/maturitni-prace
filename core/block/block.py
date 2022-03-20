from __future__ import annotations

import struct
from collections import defaultdict
from contextlib import suppress
from hashlib import sha256
from math import ceil
from time import time
from typing import Sequence, Dict, Tuple, List, Any, TYPE_CHECKING, Set

from core import bytetools

if TYPE_CHECKING:
    from core.transaction import Transaction, CoinbaseTransaction, TransactionOutpoint


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

    def unspent_outpoints(self, addresses: Sequence[bytes] = None) -> Set[TransactionOutpoint]:
        assert addresses is None or all(isinstance(address, bytes) and len(address) == 8 for address in addresses), \
            'Addresses must be a sequence of bytes[8].'

        from core.transaction import TransactionOutpoint

        transactions = self.expand_transactions()
        unspent_outpoints: Set[TransactionOutpoint] = set()

        for transaction in transactions.values():
            for tx_input in transaction.inputs:
                # KeyErrors are going to be raised in case that 'addresses' argument is provided
                # This function should be executed only on checked blockchain, so suppressing the exception is safe
                with suppress(KeyError):
                    unspent_outpoints.remove(tx_input.outpoint)

            for i, tx_output in enumerate(transaction.outputs):
                if tx_output.address in addresses:
                    unspent_outpoints.add(TransactionOutpoint(transaction.id(), i))

        return unspent_outpoints

    def balances(self, unspent_outpoints: Set[TransactionOutpoint]) -> Dict:
        from core.transaction import TransactionOutpoint

        assert isinstance(unspent_outpoints, set) \
               and all(isinstance(outpoint, TransactionOutpoint) for outpoint in unspent_outpoints), \
            'Unspent outpoints have to be a set of TransactionOutpoint instances.'

        transactions = self.expand_transactions()
        balances = defaultdict(lambda: 0)

        for unspent_outpoint in unspent_outpoints:
            tx_output = transactions[unspent_outpoint.transaction_id].outputs[unspent_outpoint.output_index]
            balances[tx_output.address] += tx_output.amount

        return balances

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

    def check_proof(self) -> bool:
        # TODO: Should check for proof of linked blocks too

        return self.id() < (bytes(4) + b'\xff' * 28)

    def check_transactions(self) -> bool:
        # TODO: Check that transactions are signed

        from core.transaction import TransactionOutpoint, CoinbaseTransaction

        blocks = self.expand_chain()
        transactions: Dict = {}
        unspent_outpoints: Set[TransactionOutpoint] = set()

        for block in blocks:
            block_transactions = {}

            for transaction in block.transactions:
                amount_available = amount_spent = 0

                for tx_input in transaction.inputs:
                    try:
                        ref_transaction = transactions[tx_input.outpoint.transaction_id]
                        ref_output = ref_transaction.outputs[tx_input.outpoint.output_index]
                        amount_available += ref_output.amount

                        unspent_outpoints.remove(tx_input.outpoint)
                    except KeyError:
                        return False

                for i, tx_output in enumerate(transaction.outputs):
                    amount_spent += tx_output.amount

                    unspent_outpoints.add(TransactionOutpoint(transaction.id(), i))

                if amount_spent > amount_available and not isinstance(transaction, CoinbaseTransaction):
                    return False

                block_transactions[transaction.id()] = transaction

            transactions |= block_transactions

        return True

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
