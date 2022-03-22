import typer

from core.block import Block
from core.helpers import BlockchainHelper
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
    if latest_block is None:
        print('Blockchain not yet initialized.')
        return

    # Calculate balances from unspent outpoints
    unspent_outpoints = latest_block.unspent_outpoints((wallet.address(),))
    balances = Block.sum_unspent_outpoints(unspent_outpoints)

    # Print current balance
    print(f'\nCurrent balance for {wallet.address().hex()}: {balances[wallet.address()]}\nUnspent outpoints:')

    # Iterate over unspent outpoints and print out it's amount
    for unspent_outpoint, tx_output in unspent_outpoints.items():
        print(f'- {unspent_outpoint.transaction_id.hex()}[{unspent_outpoint.output_index}]: {tx_output.amount}')
