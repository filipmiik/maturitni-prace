from __future__ import annotations

import struct
from collections import defaultdict, OrderedDict
from contextlib import suppress
from hashlib import sha256
from math import ceil
from time import time
from typing import Sequence, Dict, Tuple, Any, TYPE_CHECKING

from core.helpers.bytes import BytesHelper

if TYPE_CHECKING:
    from core.transaction import Transaction, CoinbaseTransaction, TransactionOutpoint, TransactionOutput


class Block:
    def __init__(self, previous_block: Block | None, transactions: Sequence[Transaction]):
        """
        Create a new block.

        :param previous_block: an instance of the previous block or None if genesis block
        :param transactions: a sequence of all transactions that a block should include
        """

        from core.block import GenesisBlock
        from core.transaction import Transaction, CoinbaseTransaction

        assert isinstance(previous_block, Block) or isinstance(self, GenesisBlock), \
            'Argument `previous_block` has to be an instance of Block.'
        assert isinstance(transactions, Sequence) \
               and all(isinstance(transaction, Transaction) for transaction in transactions), \
            'Argument `transactions` has to be a sequence of valid Transaction instances.'
        assert sum(isinstance(transaction, CoinbaseTransaction) for transaction in transactions) <= 1, \
            'Provided transactions may include only one instance of CoinbaseTransaction.'

        self.previous_block = previous_block
        self.transactions = tuple(transactions)
        self.timestamp = ceil(time() * 1000)
        self.nonce = 0

    def __bytes__(self):
        return b''.join([
            self.block_header(),
            BytesHelper.from_array(self.transactions),
        ])

    def __eq__(self, other: Any):
        return bytes(other) == self.__bytes__()

    def __hash__(self):
        return hash(self.__bytes__())

    def id(self) -> bytes:
        """
        Calculate the block's ID.

        :return: the hash digest of the block header
        """

        return sha256(self.block_header()).digest()

    def block_header(self) -> bytes:
        """
        Get the serialized block header.

        :return: the serialized block header
        """

        from core.transaction import Transaction

        return b''.join([
            self.previous_block.id(),
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
            'previous_block_id': self.previous_block.id().hex(),
            'transactions_root': Transaction.calculate_merkle_root(self.transactions).hex(),
            'timestamp': self.timestamp,
            'nonce': self.nonce,
            'transactions': tuple(transaction.json() for transaction in self.transactions)
        }

    def unspent_outpoints(self, addresses: Sequence[bytes] = None) -> Dict[TransactionOutpoint, TransactionOutput]:
        """
        Find the unspent outpoints in the whole blockchain.

        :param addresses: the addresses to limit the search to, if None all unspent outpoints are found
        :return: a dictionary of outpoints as keys and the referenced transaction outputs as values
        """

        assert addresses is None or all(isinstance(address, bytes) and len(address) == 8 for address in addresses), \
            'Argument `addresses` must be a sequence of bytes[8].'

        from core.transaction import TransactionOutpoint

        # Get all transactions in the blockchain to this block
        transactions = self.expand_transactions()
        unspent_outpoints: Dict[TransactionOutpoint, TransactionOutput] = {}

        # Iterate over the transactions
        for transaction in transactions.values():
            # Remove outpoints referenced by transaction's inputs from unspent outpoints
            for tx_input in transaction.inputs:
                # KeyErrors are going to be raised in case that 'addresses' argument is provided
                # This function should be executed only on checked blockchain, so suppressing the exception is safe
                with suppress(KeyError):
                    del unspent_outpoints[tx_input.outpoint]

            # Add outpoints created by transaction's outputs to the unspent outpoints
            for i, tx_output in enumerate(transaction.outputs):
                if addresses is None or tx_output.address in addresses:
                    unspent_outpoints[TransactionOutpoint(transaction.id(), i)] = tx_output

        return unspent_outpoints

    def valid(self, shallow: bool = True) -> bool:
        """
        Check if the block or blockchain is valid.

        :param shallow: if True, checks the validity only of this block
        :return: the validity value
        """

        return self.valid_proof(shallow) and self.valid_transactions(shallow)

    def valid_proof(self, shallow: bool = True) -> bool:
        """
        Check if the block's or blockchain's proof(s) is/are valid.

        :param shallow: if True, checks the validity only of this block
        :return: the validity value
        """

        # Expand the blockchain to check all blocks if needed
        blocks = (self,) if shallow else self.expand_chain().values()

        # Iterate over blocks:
        for block in blocks:
            # Check if proof is valid
            if block.id() >= (bytes(2) + b'\xff' * 30):
                return False

        return True

    def valid_transactions(self, shallow: bool = True) -> bool:
        """
        Check if the block's or blockchain's transactions are valid.

        :param shallow: if True, checks the validity only of this block
        :return: the validity value
        """

        # Expand the blockchain to check transactions per-block if needed
        blocks = (self,) if shallow else self.expand_chain().values()

        # Iterate over blocks
        for block in blocks:
            transactions = block.transactions

            # Check if all transactions are valid
            if any(not transaction.valid(block.previous_block) for transaction in transactions):
                return False

        return True

    def expand_chain(self) -> Dict[bytes, Block]:
        """
        Expand the whole blockchain up to this block.

        :return: a dictionary of block ids as keys and blocks as values
        """

        blocks: OrderedDict[bytes, Block] = OrderedDict({
            self.id(): self
        })
        block = self

        # Loop while there is a previous block
        while isinstance(block := block.previous_block, Block):
            blocks[block.id()] = block

        # Reverse the dictionary key order to represent timeline
        blocks = OrderedDict(reversed(blocks.items()))

        return blocks

    def expand_transactions(self) -> Dict[bytes, Transaction]:
        """
        Extract all transactions from the whole blockchain up to this block.

        :return: a dictionary of transactions ids as keys and transactions as values
        """

        transactions = {}

        # Iterate over all blocks and extract transactions from them
        for block in self.expand_chain().values():
            for transaction in block.transactions:
                transactions[transaction.id()] = transaction

        return transactions

    @staticmethod
    def sum_unspent_outpoints(unspent_outpoints: Dict[TransactionOutpoint, TransactionOutput]) \
            -> Dict[bytes, float]:
        """
        Sum the values of unspent outpoints for included addresses.

        :param unspent_outpoints: the unspent outpoints to sum
        :return: a dictionary of addresses as keys and balances as values
        """

        from core.transaction import TransactionOutpoint, TransactionOutput

        assert isinstance(unspent_outpoints, dict) \
               and all(isinstance(outpoint, TransactionOutpoint) and isinstance(amount, TransactionOutput)
                       for outpoint, amount in unspent_outpoints.items()), \
            'Argument `unspent_outpoints` has to be a Dict[TransactionOutpoint, TransactionOutput].'

        # Initialize the balances as a dictionary with default value of 0
        balances = defaultdict(lambda: 0.0)

        # Iterate over the outpoints and add their values to the total balance
        for outpoint, tx_output in unspent_outpoints.items():
            balances[tx_output.address] += tx_output.amount

        return balances

    @classmethod
    def from_bytes(cls, b: bytes, previous_block: Block) -> Tuple[bytes, Block]:
        """
        Deserialize a block from provided bytes and append it to the previous block.

        :param b: the serialized block bytes
        :param previous_block: the previous block
        :return: a tuple containing the remaining bytes and the deserialized block
        """

        from core.transaction import Transaction

        with BytesHelper.load_safe(b):
            # Load previous block ID
            b, previous_block_id = BytesHelper.load_raw_data(b, 32)

            if previous_block_id != previous_block.id():
                raise ValueError('Loaded previous block ID has to match provided previous block ID.')

            # Load other block properties
            b, merkle_root = BytesHelper.load_raw_data(b, 32)
            b, timestamp = b[8:], struct.unpack('>q', b[:8])[0]
            b, nonce = b[8:], struct.unpack('>q', b[:8])[0]
            b, transactions = BytesHelper.to_array(b, Transaction)

            if merkle_root != Transaction.calculate_merkle_root(transactions):
                raise ValueError('Loaded merkle root has to match calculated merkle root.')

        # Create the new block
        block = Block(previous_block, transactions)
        block.timestamp = timestamp
        block.nonce = nonce

        return b, block
