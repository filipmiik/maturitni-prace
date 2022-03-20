from datetime import datetime

import typer

from core.helper import BlockchainHelper, TransactionHelper
from core.transaction import TransactionInput, TransactionOutput, Transaction
from ._app import app
from ._helper import CLIHelper


@app.command()
def transfer(
        from_address: str = typer.Argument(..., help='The sending wallet address'),
        to_address: str = typer.Argument(..., help='The receiving wallet address'),
        amount: float = typer.Argument(..., help='The amount of units to transfer')
) -> None:
    """
    Transfer specified AMOUNT of units from FROM_ADDRESS to TO_ADDRESS.
    """

    # Parse command arguments
    if amount <= 0:
        raise ValueError('AMOUNT has to be an integer greater than zero.')

    from_wallet = CLIHelper.load_wallet_by_address(from_address)
    to_wallet = CLIHelper.load_wallet_by_address(to_address)

    # Load blockchain
    print('Loading blockchain...')

    latest_block = BlockchainHelper.load_blockchain()

    # Check if sending wallet has enough funds available
    print('Validating transaction...')

    transactions = latest_block.expand_transactions()
    unspent_outpoints = latest_block.unspent_outpoints((from_wallet.address(),))
    balances = latest_block.balances(unspent_outpoints)

    if from_wallet.address() not in balances or balances[from_wallet.address()] < amount:
        raise ValueError('There are not enough funds available to execute this transaction.')

    # Prepared UTXOs to be sorted by amount
    prepared_outpoints = []

    for outpoint in unspent_outpoints:
        tx_output = transactions[outpoint.transaction_id].outputs[outpoint.output_index]
        prepared_outpoints.append((tx_output.amount, outpoint))

    prepared_outpoints.sort(key=lambda item: item[0])
    reversed(prepared_outpoints)

    # Combine prepared UTXOs to fit specified amount
    prepared_amount = 0
    prepared_outpoints = []

    while prepared_amount < amount:
        outpoint = unspent_outpoints.pop()
        tx_output = transactions[outpoint.transaction_id].outputs[outpoint.output_index]

        prepared_amount += tx_output.amount
        prepared_outpoints.append(outpoint)

    # Prepare the transaction inputs and outputs
    print('Creating transaction...')

    tx_inputs = tuple(TransactionInput(outpoint) for outpoint in prepared_outpoints)
    tx_outputs = [TransactionOutput(to_wallet.address(), amount)]

    # Return the remaining amount back to the sender if any
    if prepared_amount > amount:
        tx_outputs.append(TransactionOutput(from_wallet.address(), prepared_amount - amount))

    # Create the transaction and sign it
    transaction = Transaction(tx_inputs, tx_outputs)

    print('Signing transaction...')

    from_wallet.sign_transaction(transaction)

    # Save the new transaction into mempool
    print('Saving transaction into mempool...')

    TransactionHelper.save_transaction(transaction)

    # Print the created transaction
    date_str = datetime.fromtimestamp(transaction.timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')

    print('\nTransaction:')
    print(f'- {transaction.id().hex()} ({transaction.timestamp}, {date_str})')
    print(f'\t{amount} units from {from_address} to {to_address}')
