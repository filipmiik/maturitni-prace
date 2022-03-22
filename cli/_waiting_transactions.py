from datetime import datetime

from core.helpers import TransactionHelper
from ._app import app


@app.command()
def waiting_transactions() -> None:
    """
    List waiting transactions.
    """

    # Load transactions from mempool and sort them by timestamps
    print(f'Loading transactions from mempool...')

    transactions = list(TransactionHelper.load_waiting_transactions())
    transactions.sort(key=lambda tx: tx.timestamp)

    # Print the transactions
    print('\nTransactions:')

    for transaction in transactions:
        date_str = datetime.fromtimestamp(transaction.timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')

        # TODO: Print from address, to address and amount
        print(f'- {transaction.id().hex()} ({transaction.timestamp}, {date_str})')
