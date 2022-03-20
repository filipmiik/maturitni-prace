from typing import Set, Sequence

from core.block import GenesisBlock
from core.transaction import Transaction


class TransactionHelper:
    @staticmethod
    def load_waiting_transactions() -> Set[Transaction]:
        with open('data/mempool.bin', 'rb') as file:
            b = file.read()

        transactions = set()

        while len(b) > 0:
            b, transaction = Transaction.from_bytes(b)
            transactions.add(transaction)

        return transactions

    @staticmethod
    def save_transaction(transaction: Transaction):
        assert isinstance(transaction, Transaction), \
            'Transaction has to be an instance of Transaction.'

        with open('data/mempool.bin', 'ab') as file:
            file.write(bytes(transaction))

    @staticmethod
    def export_transactions(type: str, transactions: Sequence[Transaction]):
        assert type == 'json', \
            'Currently supported export type is only "json".'
        assert all(isinstance(transaction, Transaction) for transaction in transactions), \
            'Transactions have to be a sequence of Transaction instances.'

        pass
