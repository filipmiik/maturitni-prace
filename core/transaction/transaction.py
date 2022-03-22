from __future__ import annotations

import struct
from functools import reduce
from hashlib import sha256
from math import ceil
from time import time
from typing import TYPE_CHECKING, Sequence, List, Dict, Tuple, Any, Iterable

if TYPE_CHECKING:
    from core.block import Block
    from .transaction_input import TransactionInput
    from .transaction_output import TransactionOutput
    from .transaction_signature import TransactionSignature


class Transaction:
    def __init__(self, inputs: Sequence[TransactionInput], outputs: Sequence[TransactionOutput]):
        """
        Create a transaction from inputs and outputs.

        :param inputs: a sequence of inputs (length > 0)
        :param outputs: a sequence of outputs
        """

        from .coinbase_transaction import CoinbaseTransaction
        from .transaction_input import TransactionInput
        from .transaction_output import TransactionOutput

        assert (len(inputs) > 0 or isinstance(self, CoinbaseTransaction)) \
               and all(isinstance(tx_input, TransactionInput) for tx_input in inputs), \
            'Argument `inputs` has to be a sequence of TransactionInput instances with length > 0.'
        assert all(isinstance(tx_output, TransactionOutput) for tx_output in outputs), \
            'Argument `outputs` has to be a sequence of TransactionOutput instances.'

        self.inputs: Tuple[TransactionInput] = tuple(inputs)
        self.outputs: Tuple[TransactionOutput] = tuple(outputs)
        self.signatures: List[TransactionSignature] = []

        self.timestamp = ceil(time() * 1e3)

    def __bytes__(self):
        from core.helpers import BytesHelper

        return b''.join([
            struct.pack('>q', self.timestamp),
            BytesHelper.from_array(self.inputs),
            BytesHelper.from_array(self.outputs),
            BytesHelper.from_array(self.signatures),
        ])

    def __eq__(self, other: Any):
        return bytes(other) == self.__bytes__()

    def __hash__(self):
        return hash(self.__bytes__())

    def id(self) -> bytes:
        return sha256(self.__bytes__()).digest()

    def json(self) -> Dict[str, Any]:
        """
        Get the serialized transaction dumpable to JSON.

        :return: a dictionary containing all information about this transaction
        """

        return {
            'inputs': tuple(tx_input.json() for tx_input in self.inputs),
            'outputs': tuple(tx_output.json() for tx_output in self.outputs),
            'signatures': tuple(tx_signature.json() for tx_signature in self.signatures),
            'timestamp': self.timestamp,
        }

    def sign(self, signature: TransactionSignature) -> None:
        """
        Add signature to this transaction.

        :param signature: the signature
        """

        from .transaction_signature import TransactionSignature

        assert isinstance(signature, TransactionSignature), \
            'Argument `signature` has to be an instance of TransactionSignature.'
        assert not any(tx_signature.wallet == signature.wallet for tx_signature in self.signatures), \
            'This wallet has already signed this transaction.'

        self.signatures.append(signature)

    def valid(self, latest_block: Block | None) -> bool:
        """
        Check if this transaction is valid in blockchain defined by it's latest block.

        :param latest_block: the latest block of the checked blockchain or None
        """

        from core.block import Block

        assert latest_block is None or isinstance(latest_block, Block), \
            'Argument `latest_block` has to be an instance of Block or None.'

        # Get unspent outpoints
        unspent_outpoints = latest_block.unspent_outpoints() if isinstance(latest_block, Block) else {}

        # Check if spending only unspent outpoints and count total available amount
        total_available = 0

        for tx_input in self.inputs:
            try:
                total_available += unspent_outpoints[tx_input.outpoint].amount
                del unspent_outpoints[tx_input.outpoint]
            except KeyError:
                return False

        # Calculate total spent amount
        total_spent = reduce(lambda acc, curr: acc + curr.amount, self.outputs, 0)

        # Check if spent amount is not greater than available amount and that all inputs are signed
        return total_available >= total_spent and self._signed(latest_block)

    def _signed(self, latest_block: Block | None) -> bool:
        """
        Check if all transactions in this block are signed by their right addresses.

        :param latest_block: the latest block of the blockchain or None
        """

        from core.block import Block

        assert latest_block is None or isinstance(latest_block, Block), \
            'Argument `latest_block` has to be an instance of Block or None.'

        # Get transactions
        transactions = latest_block.expand_transactions() if isinstance(latest_block, Block) else {}

        # Get signed addresses
        signed_addresses = list(signature.wallet.address() for signature in self.signatures)

        # Check if all signed
        for tx_input in self.inputs:
            address = transactions[tx_input.outpoint.transaction_id].outputs[tx_input.outpoint.output_index].address

            if address not in signed_addresses:
                return False

        return True

    @classmethod
    def from_bytes(cls, b: bytes) -> Tuple[bytes, Transaction]:
        """
        Deserialize a transaction from provided bytes.

        :param b: the serialized transaction bytes
        :return: a tuple containing the remaining bytes and the transaction
        """

        from .transaction_input import TransactionInput
        from .transaction_output import TransactionOutput
        from .transaction_signature import TransactionSignature
        from . import CoinbaseTransaction
        from core.helpers import BytesHelper

        with BytesHelper.load_safe(b):
            # Load transaction properties
            b, timestamp = b[8:], struct.unpack('>q', b[:8])[0]
            b, inputs = BytesHelper.to_array(b, TransactionInput)
            b, outputs = BytesHelper.to_array(b, TransactionOutput)
            b, signatures = BytesHelper.to_array(b, TransactionSignature)

        # Create the transaction
        transaction = CoinbaseTransaction(outputs[0].address) if len(inputs) == 0 else Transaction(inputs, outputs)
        transaction.signatures = signatures
        transaction.timestamp = timestamp

        return b, transaction

    @staticmethod
    def calculate_merkle_root(transactions: Iterable[Transaction]) -> bytes:
        """
        Calculate merkle root from transaction IDs of provided transactions.

        :param transactions: the transactions to calculate merkle root from
        :return: the hash digest of the merkle root
        """

        from core.helpers import HashHelper

        return HashHelper.calculate_merkle_root(transaction.id() for transaction in transactions)
