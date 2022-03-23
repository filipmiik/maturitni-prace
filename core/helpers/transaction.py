import json
from typing import Set, Iterable, List, Dict

from core.transaction import Transaction


class TransactionHelper:
    @staticmethod
    def load_transactions() -> Set[Transaction]:
        """
        Load transactions from mempool that are waiting to be added to a block.

        :return: a set of waiting transactions
        """

        # Load binary data from mempool
        try:
            with open('data/mempool.bin', 'rb') as file:
                b = file.read()
        except FileNotFoundError:
            return set()

        # Deserialize transactions from raw binary data
        transactions = set()

        while len(b) > 0:
            b, transaction = Transaction.from_bytes(b)
            transactions.add(transaction)

        return transactions

    @staticmethod
    def save_transaction(transaction: Transaction) -> None:
        """
        Save provided transaction to mempool (appends to the mempool).

        :param transaction: the transaction to be saved
        """

        assert isinstance(transaction, Transaction), \
            'Transaction has to be an instance of Transaction.'

        # Append serialized transaction to the mempool
        with open('data/mempool.bin', 'ab') as file:
            file.write(bytes(transaction))

    @staticmethod
    def save_transactions(transactions: Iterable[Transaction]) -> None:
        """
        Save provided transactions to mempool (overwrites the whole mempool).

        :param transactions: an iterable of transactions
        """

        try:
            # Serialize all provided transactions to bytes
            data: List[bytes] = list(bytes(tx) for tx in transactions)
        except TypeError:
            raise TypeError('Argument `transactions` has to be an iterable of Transaction.')

        assert all(isinstance(transaction, Transaction) for transaction in transactions), \
            'Argument `transactions` has to be an iterable of Transaction.'

        # Append serialized transactions to the mempool
        with open('data/mempool.bin', 'wb') as file:
            file.write(b''.join(data))

    @staticmethod
    def export_transaction(transaction: Transaction) -> None:
        """
        Export provided transaction to mempool (appends to the mempool export).

        :param transaction: the transaction to be exported
        """

        assert isinstance(transaction, Transaction), \
            'Transaction has to be an instance of Transaction.'

        # Append serialized transaction to the mempool
        with open('data/mempool.bin', 'w+') as file:
            # Load current exported data
            data = json.load(file)
            if not isinstance(data, List):
                data = list()

            # Append the transactions to the exported data and save it
            data.append(transaction.json())
            json.dump(data, file)

    @staticmethod
    def export_transactions(transactions: Iterable[Transaction]) -> None:
        """
        Export provided transactions to JSON (overwrite the whole mempool export).

        :param transactions: an iterable of transactions
        """

        try:
            # Serialize all provided transactions to JSON
            data: List[Dict] = list(tx.json() for tx in transactions)
        except TypeError:
            raise TypeError('Argument `transactions` has to be an iterable of Transaction.')

        # Check if all transactions are instances of Transaction
        assert all(isinstance(transaction, Transaction) for transaction in transactions), \
            'Argument `transactions` has to be an iterable of Transaction.'

        # Save the exported array
        with open('data/mempool.json', 'w') as file:
            json.dump(data, file)

    @staticmethod
    def remove_transactions(transactions: Iterable[Transaction]) -> None:
        """
        Remove provided transaction from mempool.

        :param transactions: the transactions to be removed
        """

        # Load transactions from mempool
        saved_transactions = TransactionHelper.load_transactions()

        try:
            # Convert iterable to list
            transactions = list(iter(transactions))
        except TypeError:
            raise TypeError('Argument `transactions` has to be an iterable of object[Transaction].')

        # Check that all items in transactions are transaction instances
        assert all(isinstance(tx, Transaction) for tx in transactions), \
            'Argument `transactions` has to be an iterable of object[Transaction].'

        # Remove provided transactions from loaded transactions
        saved_transactions = filter(lambda tx: tx not in transactions, saved_transactions)

        # Overwrite mempool with new transactions
        TransactionHelper.save_transactions(saved_transactions)
