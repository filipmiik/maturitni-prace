import typer

from core.helper import BlockchainHelper
from ._app import app
from ._helper import CLIHelper


@app.command()
def balance(
        address: str = typer.Argument(..., help='The wallet address to show balance for')
) -> None:
    """
    Show the cumulative amount and list of UTXOs belonging to ADDRESS.
    """

    # Parse command arguments
    wallet = CLIHelper.load_wallet_by_address(address)

    # Load blockchain
    print('Loading blockchain...')

    latest_block = BlockchainHelper.load_blockchain()

    # Calculate balances from unspent outpoints
    transactions = latest_block.expand_transactions()
    unspent_outpoints = latest_block.unspent_outpoints((wallet.address(),))
    balances = latest_block.balances(unspent_outpoints)

    # Print current balance
    print(f'\nCurrent balance for {wallet.address().hex()}: {balances[wallet.address()]}\nUnspent outpoints:')

    # Iterate over unspent outpoints and print out it's amount
    for unspent_outpoint in unspent_outpoints:
        tx_output = transactions[unspent_outpoint.transaction_id].outputs[unspent_outpoint.output_index]

        print(f'- {unspent_outpoint.transaction_id.hex()}[{unspent_outpoint.output_index}]: {tx_output.amount}')
